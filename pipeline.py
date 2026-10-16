"""Earthquake ingestion and facility screening. No damage or prediction model."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib
import json
import logging
import math
import sqlite3
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

LOG = logging.getLogger(__name__)
AFAD_URL = 'https://deprem.afad.gov.tr/apiv2/event/filter'
PROVINCE_URL = 'https://turkiyeapi.dev/api/v1/provinces'


def fetch_json(url, params, raw_dir, attempts=3):
    """Timeout, bounded retries, TLS verification, and immutable raw snapshots."""
    request_url = url + '?' + urlencode(params)
    for attempt in range(attempts):
        try:
            request = Request(request_url, headers={'User-Agent': 'EarthquakeAnalyticsPortfolio/1.0'})
            with urlopen(request, timeout=30) as response:
                payload = json.load(response)
            break
        except HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == attempts - 1:
                raise
            time.sleep(min(2 ** attempt, 8))
        except URLError:
            if attempt == attempts - 1:
                raise
            time.sleep(min(2 ** attempt, 8))
    envelope = {'url': request_url, 'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
                'payload': payload}
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(request_url.encode()).hexdigest()[:16]
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    (raw_dir / f'{stamp}_{key}.json').write_text(json.dumps(envelope, ensure_ascii=False), encoding='utf-8')
    return payload


def fetch_events(start, end, raw_dir, source_timezone, fetcher=fetch_json, limit=1000):
    """Fetch daily windows; split saturated windows instead of silently truncating.

    start/end are naive source-clock datetimes; end is exclusive. API time-zone
    semantics must be verified by the caller before running live. Adjacent windows
    may overlap at endpoints; normalization resolves repeated event IDs.
    """
    if not source_timezone or start.tzinfo or end.tzinfo or start >= end or limit < 2:
        raise ValueError('Provide a verified source timezone, naive start < end, and limit >= 2.')
    if start.microsecond or end.microsecond:
        raise ValueError('Query boundaries must be whole seconds.')
    def window(lo, hi):
        params = {'start': lo.isoformat(sep=' '), 'end': hi.isoformat(sep=' '), 'limit': limit}
        rows = fetcher(AFAD_URL, params, raw_dir)
        if not isinstance(rows, list) or any(not isinstance(x, dict) for x in rows):
            raise ValueError('AFAD schema changed: expected a list of event objects.')
        if len(rows) >= limit:
            seconds = int((hi - lo).total_seconds())
            if seconds <= 1:
                raise RuntimeError('Saturated one-second window: completeness cannot be established.')
            mid = lo + timedelta(seconds=seconds // 2)
            return window(lo, mid) + window(mid, hi)
        LOG.info('Fetched %s records for %s to %s', len(rows), lo, hi)
        return rows
    rows = []
    cursor = start
    while cursor < end:
        stop = min(cursor + timedelta(days=1), end)
        rows.extend(window(cursor, stop))
        cursor = stop
    return rows


def name_key(value):
    if value is None or pd.isna(value):
        return ''
    value = str(value).strip().replace('İ', 'I').replace('ı', 'i').casefold()
    return ''.join(c for c in unicodedata.normalize('NFKD', value) if not unicodedata.combining(c))


def province_tables(payload):
    """Separate grains; district IDs and names never overwrite province columns."""
    if not isinstance(payload, dict) or not isinstance(payload.get('data'), list):
        raise ValueError('Expected TurkiyeAPI object with a data list.')
    provinces, districts = [], []
    for p in payload['data']:
        provinces.append({'province_id': int(p['id']), 'province_name': p['name'],
                          'province_key': name_key(p['name']), 'region': (p.get('region') or {}).get('en')})
        for d in p.get('districts') or []:
            districts.append({'district_id': int(d['id']), 'district_name': d['name'],
                              'province_id': int(p['id'])})
    provinces = pd.DataFrame(provinces, columns=['province_id', 'province_name', 'province_key', 'region'])
    districts = pd.DataFrame(districts, columns=['district_id', 'district_name', 'province_id'])
    if provinces.empty or (provinces.province_id <= 0).any() or (provinces.province_key == '').any():
        raise ValueError('Invalid/empty province reference data.')
    if provinces.province_id.duplicated().any() or provinces.province_key.duplicated().any():
        raise ValueError('Ambiguous province IDs or normalized names.')
    if districts.district_id.duplicated().any():
        raise ValueError('Duplicate district IDs.')
    unknown = pd.DataFrame([{'province_id': 0, 'province_name': 'Unmatched / outside reference',
                             'province_key': '', 'region': None}])
    return pd.concat([unknown, provinces], ignore_index=True), districts


def parse_time(value, source_timezone):
    try:
        ts = pd.Timestamp(value)
        if pd.isna(ts):
            return pd.NaT
        if ts.tzinfo is None:
            ts = ts.tz_localize(source_timezone, ambiguous='raise', nonexistent='raise')
        return ts.tz_convert('UTC')
    except (ValueError, TypeError):
        return pd.NaT


def normalize_events(records, provinces, source_timezone, start=None, end=None):
    """Quarantine invalid rows; use latest source update for duplicate IDs.

    Negative magnitude is valid. Missing magnitude/depth is retained and counted,
    never replaced with zero. Unknown province uses explicit key 0, not a guessed
    nearest province. A source province label is not a polygon spatial assignment.
    """
    columns = ['eventID', 'date', 'latitude', 'longitude', 'magnitude', 'depth',
               'type', 'province', 'country', 'location', 'lastUpdateDate']
    frame = pd.DataFrame(records)
    required = {'eventID', 'date', 'latitude', 'longitude'}
    if len(frame) and not required.issubset(frame.columns):
        raise ValueError(f'Missing event fields: {required - set(frame.columns)}')
    frame = frame.reindex(columns=columns).copy()
    frame['event_id'] = frame.eventID.astype('string').str.strip()
    frame['event_time_utc'] = pd.to_datetime(frame.date.map(lambda v: parse_time(v, source_timezone)), utc=True)
    frame['updated_at'] = pd.to_datetime(frame.lastUpdateDate.map(lambda v: parse_time(v, source_timezone)), utc=True)
    reasons = pd.Series('', index=frame.index)
    def flag(mask, reason):
        reasons.loc[mask.fillna(True)] += reason + ';'
    flag(frame.event_id.isna() | frame.event_id.eq(''), 'missing_event_id')
    flag(frame.event_time_utc.isna(), 'invalid_timestamp')
    for column in ['latitude', 'longitude', 'magnitude', 'depth']:
        source = frame[column]
        converted = pd.to_numeric(source, errors='coerce')
        missing = source.isna() | source.astype('string').str.strip().eq('')
        flag((~missing) & (converted.isna() | ~np.isfinite(converted)), f'invalid_{column}')
        frame[column] = converted
    flag(~frame.latitude.between(-90, 90), 'latitude_out_of_range')
    flag(~frame.longitude.between(-180, 180), 'longitude_out_of_range')
    flag(frame.depth.notna() & frame.depth.lt(0), 'negative_depth')
    rejected = frame.loc[reasons.ne('')].copy()
    rejected['rejection_reason'] = reasons[reasons.ne('')]
    valid = frame.loc[reasons.eq('')].copy()
    # Keep half-open query scope even when the provider includes both endpoints.
    outside = pd.Series(False, index=valid.index)
    if start is not None:
        outside |= valid.event_time_utc.lt(parse_time(start, source_timezone))
    if end is not None:
        outside |= valid.event_time_utc.ge(parse_time(end, source_timezone))
    out_of_scope = int(outside.sum())
    valid = valid.loc[~outside]
    valid = valid.sort_values('updated_at', na_position='first', kind='stable')
    duplicate_rows = valid.loc[valid.event_id.duplicated(keep='last')].copy()
    valid = valid.drop_duplicates('event_id', keep='last')
    valid['province_key'] = valid.province.map(name_key)
    valid = valid.merge(provinces[['province_key', 'province_id']], on='province_key', how='left', validate='many_to_one')
    valid['province_id'] = valid.province_id.fillna(0).astype('int64')
    valid['date_key'] = valid.event_time_utc.dt.strftime('%Y%m%d').astype('int64')
    valid = valid.rename(columns={'depth': 'depth_km', 'type': 'magnitude_type', 'province': 'source_province'})
    fields = ['event_id', 'event_time_utc', 'date_key', 'province_id', 'latitude', 'longitude',
              'magnitude', 'magnitude_type', 'depth_km', 'country', 'source_province', 'location']
    valid = valid[fields].sort_values(['event_time_utc', 'event_id']).reset_index(drop=True)
    quality = {'raw_rows': len(frame), 'rejected_rows': len(rejected), 'out_of_scope_rows': out_of_scope,
               'duplicate_rows_removed': len(duplicate_rows), 'accepted_events': len(valid),
               'unmatched_province_events': int(valid.province_id.eq(0).sum()),
               'missing_magnitude_events': int(valid.magnitude.isna().sum()),
               'missing_depth_events': int(valid.depth_km.isna().sum())}
    assert sum(quality[k] for k in ['rejected_rows', 'out_of_scope_rows', 'duplicate_rows_removed', 'accepted_events']) == len(frame)
    return valid, rejected, duplicate_rows, quality


def date_dimension(start, end):
    dates = pd.date_range(pd.Timestamp(start).date(), pd.Timestamp(end).date(), freq='D')
    return pd.DataFrame({'date_key': dates.strftime('%Y%m%d').astype(int), 'date': dates.strftime('%Y-%m-%d'),
                         'year': dates.year, 'month': dates.month, 'month_name': dates.month_name(),
                         'quarter': dates.quarter})


def validate_facilities(facilities, provinces, allow_synthetic=False):
    fields = ['facility_id', 'facility_name', 'facility_type', 'province_id', 'latitude', 'longitude',
              'source_url', 'verified_on', 'coordinate_quality', 'is_synthetic']
    if not set(fields).issubset(facilities.columns):
        raise ValueError('Facility input must match data/facilities_template.csv.')
    f = facilities[fields].copy()
    if f.empty:
        return f
    for c in ['facility_id', 'facility_name', 'facility_type', 'source_url', 'coordinate_quality']:
        if f[c].isna().any() or f[c].astype(str).str.strip().eq('').any():
            raise ValueError(f'Missing facility field: {c}')
    if f.facility_id.duplicated().any():
        raise ValueError('Duplicate facility IDs.')
    flags = f.is_synthetic.astype(str).str.lower().map({'true': True, 'false': False})
    if flags.isna().any() or (flags.any() and not allow_synthetic):
        raise ValueError('Synthetic facilities require explicit demo mode.')
    f['is_synthetic'] = flags
    for c, lower, upper in [('latitude', -90, 90), ('longitude', -180, 180)]:
        f[c] = pd.to_numeric(f[c], errors='coerce')
        if not f[c].between(lower, upper).all():
            raise ValueError(f'Invalid facility {c}')
    f['province_id'] = pd.to_numeric(f.province_id, errors='raise')
    if not f.province_id.isin(provinces.province_id).all():
        raise ValueError('Facility province foreign key missing.')
    if pd.to_datetime(f.verified_on, errors='coerce').isna().any():
        raise ValueError('Invalid verification date.')
    if not f.coordinate_quality.isin(['verified_site', 'approximate', 'synthetic']).all():
        raise ValueError('Unknown coordinate quality.')
    return f


def facility_distances(events, facilities, event_id):
    """All facilities for ONE selected event, not an unbounded cross join."""
    event = events.loc[events.event_id.eq(str(event_id))]
    if len(event) != 1:
        raise ValueError('Select one existing, unique event ID.')
    e = event.iloc[0]
    f = facilities.copy()
    lat1, lon1 = np.radians([float(e.latitude), float(e.longitude)])
    lat2, lon2 = np.radians(f.latitude.to_numpy(dtype=float)), np.radians(f.longitude.to_numpy(dtype=float))
    a = np.sin((lat2-lat1)/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin((lon2-lon1)/2)**2
    f['distance_km'] = 6371.0088 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    f['event_id'] = str(event_id)
    return f[['event_id', 'facility_id', 'distance_km']].sort_values('distance_km').reset_index(drop=True)


def export_model(tables, quality, output_dir, metadata):
    """New snapshot per run; CSV for Power BI and SQLite for reproducible SQL."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    for name, df in tables.items():
        df.to_csv(output_dir / f'{name}.csv', index=False, encoding='utf-8-sig')
    with sqlite3.connect(output_dir / 'analytics.sqlite') as conn:
        for name, df in tables.items():
            df.to_sql(name, conn, if_exists='fail', index=False)
        for table, key in [('dim_province','province_id'), ('dim_date','date_key'),
                           ('dim_facility','facility_id'), ('fact_earthquake','event_id')]:
            conn.execute(f'CREATE UNIQUE INDEX uq_{table} ON {table}({key})')
        conn.execute('CREATE UNIQUE INDEX uq_distance ON fact_event_facility(event_id, facility_id)')
        for fk, dim, key in [('province_id','dim_province','province_id'), ('date_key','dim_date','date_key')]:
            missing = conn.execute(f'SELECT COUNT(*) FROM fact_earthquake f LEFT JOIN {dim} d ON f.{fk}=d.{key} WHERE d.{key} IS NULL').fetchone()[0]
            if missing:
                raise ValueError(f'Missing foreign keys: {fk}')
    manifest = {**metadata, 'created_at_utc': datetime.now(timezone.utc).isoformat(), 'quality': quality,
                'tables': {name: {'rows': len(df), 'sha256': hashlib.sha256((output_dir/f'{name}.csv').read_bytes()).hexdigest()} for name,df in tables.items()}}
    (output_dir/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return output_dir
