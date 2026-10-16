import tempfile
import unittest
from datetime import datetime
from pathlib import Path
import pandas as pd
from pipeline import *

def provinces():
    return province_tables({'data':[{'id':35,'name':'İzmir','districts':[{'id':1,'name':'Konak'}]}]})

def event(**kwargs):
    return {'eventID':'e1','date':'2024-01-01T00:00:00','latitude':'38','longitude':'27',
            'depth':'0','magnitude':'-0.2','type':'ML','province':'İZMİR',**kwargs}

class PipelineTests(unittest.TestCase):
    def test_grains(self):
        p,d=provinces()
        self.assertEqual(d.iloc[0].district_name,'Konak')
        self.assertEqual(d.iloc[0].province_id,35)
        self.assertEqual(len(p.columns),len(set(p.columns)))

    def test_quality_and_latest_revision(self):
        p,_=provinces()
        rows=[event(),event(magnitude='2',lastUpdateDate='2024-01-02'),
              event(eventID='bad',latitude='99'),event(eventID='empty',magnitude=None,depth=None,province='Unknown')]
        f,q,duplicates,stats=normalize_events(rows,p,'UTC')
        self.assertEqual(len(f),2)
        self.assertEqual(f.loc[f.event_id.eq('e1'),'magnitude'].iloc[0],2)
        self.assertEqual(stats['rejected_rows'],1)
        self.assertEqual(stats['duplicate_rows_removed'],1)
        self.assertEqual(stats['unmatched_province_events'],1)
        self.assertEqual(stats['missing_magnitude_events'],1)

    def test_scope_and_timezone(self):
        p,_=provinces()
        f,*_=normalize_events([event(),event(eventID='end',date='2024-01-02')],p,'Europe/Istanbul',
                             '2024-01-01','2024-01-02')
        self.assertEqual(len(f),1)
        self.assertEqual(f.iloc[0].date_key,20231231)

    def test_valid_negative_magnitude_and_zero_depth(self):
        f,*_=normalize_events([event()],provinces()[0],'UTC')
        self.assertEqual(f.iloc[0].magnitude,-0.2)
        self.assertEqual(f.iloc[0].depth_km,0)

    def test_invalid_numeric_and_missing_id(self):
        f,q,_,stats=normalize_events([event(eventID=None),event(eventID='x',magnitude='oops'),
                                    event(eventID='y',longitude='inf')],provinces()[0],'UTC')
        self.assertTrue(f.empty)
        self.assertEqual(stats['rejected_rows'],3)

    def test_empty_catalogue(self):
        f,*_=normalize_events([],provinces()[0],'UTC')
        self.assertTrue(f.empty)

    def test_saturation_is_split(self):
        calls=[]
        def fake(url,params,raw):
            calls.append(params)
            duration=datetime.fromisoformat(params['end'])-datetime.fromisoformat(params['start'])
            return [event(),event()] if duration.total_seconds()>43200 else [event()]
        rows=fetch_events(datetime(2024,1,1),datetime(2024,1,2),'.','UTC',fetcher=fake,limit=2)
        self.assertEqual(len(calls),3)
        self.assertEqual(len(rows),2)

    def test_unsplittable_cap_raises(self):
        with self.assertRaises(RuntimeError):
            fetch_events(datetime(2024,1,1),datetime(2024,1,1,0,0,1),'.','UTC',
                         fetcher=lambda *args:[event(),event()],limit=2)

    def test_distance(self):
        f,*_=normalize_events([event(latitude=0,longitude=0)],provinces()[0],'UTC')
        sites=pd.DataFrame({'facility_id':['same','one_degree'],'latitude':[0,0],'longitude':[0,1]})
        distances=facility_distances(f,sites,'e1')
        self.assertEqual(distances.iloc[0].distance_km,0)
        self.assertAlmostEqual(distances.iloc[1].distance_km,111.195,places=2)
        self.assertEqual(sum(distances.distance_km.le(100)),1)

    def test_facility_provenance_and_synthetic_gate(self):
        p,_=provinces()
        f=pd.DataFrame([{'facility_id':'s1','facility_name':'Demo','facility_type':'Store',
            'province_id':35,'latitude':38,'longitude':27,'source_url':'synthetic://test',
            'verified_on':'2024-01-01','coordinate_quality':'synthetic','is_synthetic':True}])
        with self.assertRaises(ValueError): validate_facilities(f,p)
        self.assertEqual(len(validate_facilities(f,p,allow_synthetic=True)),1)
        f['province_id']=999
        with self.assertRaises(ValueError): validate_facilities(f,p,allow_synthetic=True)

    def test_schema_drift_rejected(self):
        with self.assertRaises(ValueError): normalize_events([{'id':'unexpected'}],provinces()[0],'UTC')

    def test_repeated_exports_are_identical_and_non_destructive(self):
        p,d=provinces()
        f,rejected,duplicates,quality=normalize_events([event()],p,'UTC')
        sites=pd.read_csv(Path(__file__).parent/'data/facilities_template.csv')
        tables={'dim_province':p,'dim_district':d,'dim_date':date_dimension('2024-01-01','2024-01-02'),
                'dim_facility':sites,'fact_earthquake':f,
                'fact_event_facility':pd.DataFrame(columns=['event_id','facility_id','distance_km'])}
        with tempfile.TemporaryDirectory() as tmp:
            a=export_model(tables,quality,Path(tmp)/'a',{'mode':'test'})
            b=export_model(tables,quality,Path(tmp)/'b',{'mode':'test'})
            self.assertEqual((a/'fact_earthquake.csv').read_bytes(),(b/'fact_earthquake.csv').read_bytes())
            with self.assertRaises(FileExistsError): export_model(tables,quality,a,{})

if __name__=='__main__': unittest.main()
