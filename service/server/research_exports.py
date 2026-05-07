"""Research CSV export helpers."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Optional

from database import get_db_connection


CHALLENGE_EXPORTS: dict[str, dict[str, Any]] = {
    'challenges.csv': {
        'table': 'challenges',
        'alias': 'c',
        'columns': [
            'id', 'challenge_key', 'title', 'description', 'market', 'symbol',
            'challenge_type', 'status', 'scoring_method', 'initial_capital',
            'max_position_pct', 'max_drawdown_pct', 'start_at', 'end_at',
            'settled_at', 'rules_json', 'experiment_key', 'created_by_agent_id',
            'created_at', 'updated_at',
        ],
    },
    'challenge_participants.csv': {
        'table': 'challenge_participants',
        'alias': 'cp',
        'join': 'JOIN challenges c ON c.id = cp.challenge_id',
        'columns': [
            'id', 'challenge_id', 'agent_id', 'status', 'variant_key', 'joined_at',
            'starting_cash', 'ending_value', 'return_pct', 'max_drawdown',
            'trade_count', 'rank', 'disqualified_reason',
        ],
    },
    'challenge_submissions.csv': {
        'table': 'challenge_submissions',
        'alias': 'cs',
        'join': 'JOIN challenges c ON c.id = cs.challenge_id',
        'columns': [
            'id', 'challenge_id', 'agent_id', 'signal_id', 'submission_type',
            'content', 'prediction_json', 'created_at',
        ],
    },
    'challenge_trades.csv': {
        'table': 'challenge_trades',
        'alias': 'ct',
        'join': 'JOIN challenges c ON c.id = ct.challenge_id',
        'columns': [
            'id', 'challenge_id', 'agent_id', 'source_signal_id', 'market',
            'symbol', 'side', 'price', 'quantity', 'executed_at', 'created_at',
        ],
    },
    'challenge_results.csv': {
        'table': 'challenge_results',
        'alias': 'cr',
        'join': 'JOIN challenges c ON c.id = cr.challenge_id',
        'columns': [
            'id', 'challenge_id', 'agent_id', 'return_pct', 'max_drawdown',
            'risk_adjusted_score', 'quality_score', 'final_score', 'rank',
            'metrics_json', 'settled_at',
        ],
    },
}


TEAM_MISSION_EXPORTS: dict[str, dict[str, Any]] = {
    'team_missions.csv': {
        'table': 'team_missions',
        'alias': 'tm',
        'columns': [
            'id', 'mission_key', 'title', 'description', 'market', 'symbol',
            'mission_type', 'status', 'team_size_min', 'team_size_max',
            'assignment_mode', 'required_roles_json', 'start_at',
            'submission_due_at', 'settled_at', 'rules_json', 'experiment_key',
            'created_at', 'updated_at',
        ],
    },
    'teams.csv': {
        'table': 'teams',
        'alias': 't',
        'join': 'JOIN team_missions tm ON tm.id = t.mission_id',
        'columns': [
            'id', 'mission_id', 'team_key', 'name', 'status',
            'formation_method', 'variant_key', 'created_at', 'updated_at',
        ],
    },
    'team_members.csv': {
        'table': 'team_members',
        'alias': 'tmem',
        'join': 'JOIN teams t ON t.id = tmem.team_id JOIN team_missions tm ON tm.id = t.mission_id',
        'columns': ['id', 'team_id', 'agent_id', 'role', 'status', 'joined_at'],
    },
    'team_messages.csv': {
        'table': 'team_messages',
        'alias': 'tmsg',
        'join': 'JOIN teams t ON t.id = tmsg.team_id JOIN team_missions tm ON tm.id = t.mission_id',
        'columns': ['id', 'team_id', 'agent_id', 'signal_id', 'message_type', 'content', 'metadata_json', 'created_at'],
    },
    'team_submissions.csv': {
        'table': 'team_submissions',
        'alias': 'ts',
        'join': 'JOIN team_missions tm ON tm.id = ts.mission_id',
        'columns': ['id', 'mission_id', 'team_id', 'submitted_by_agent_id', 'title', 'content', 'prediction_json', 'confidence', 'created_at'],
    },
    'team_contributions.csv': {
        'table': 'team_contributions',
        'alias': 'tc',
        'join': 'JOIN team_missions tm ON tm.id = tc.mission_id',
        'columns': ['id', 'mission_id', 'team_id', 'agent_id', 'source_type', 'source_id', 'contribution_type', 'contribution_score', 'metadata_json', 'created_at'],
    },
    'team_results.csv': {
        'table': 'team_results',
        'alias': 'tr',
        'join': 'JOIN team_missions tm ON tm.id = tr.mission_id',
        'columns': ['id', 'mission_id', 'team_id', 'return_pct', 'prediction_score', 'quality_score', 'consensus_gain', 'final_score', 'rank', 'metrics_json', 'settled_at'],
    },
}


def _build_challenge_filters(
    alias: str,
    *,
    start_at: Optional[str] = None,
    end_at: Optional[str] = None,
    experiment_key: Optional[str] = None,
    challenge_key: Optional[str] = None,
    market: Optional[str] = None,
) -> tuple[str, list[Any]]:
    conditions = []
    params: list[Any] = []
    challenge_alias = alias if alias == 'c' else 'c'

    if start_at:
        conditions.append(f"{challenge_alias}.end_at >= ?")
        params.append(start_at)
    if end_at:
        conditions.append(f"{challenge_alias}.start_at <= ?")
        params.append(end_at)
    if experiment_key:
        conditions.append(f"{challenge_alias}.experiment_key = ?")
        params.append(experiment_key)
    if challenge_key:
        conditions.append(f"{challenge_alias}.challenge_key = ?")
        params.append(challenge_key)
    if market:
        conditions.append(f"{challenge_alias}.market = ?")
        params.append(market)

    return (' WHERE ' + ' AND '.join(conditions)) if conditions else '', params


def _build_team_filters(
    alias: str,
    *,
    start_at: Optional[str] = None,
    end_at: Optional[str] = None,
    experiment_key: Optional[str] = None,
    mission_key: Optional[str] = None,
    market: Optional[str] = None,
) -> tuple[str, list[Any]]:
    conditions = []
    params: list[Any] = []
    mission_alias = alias if alias == 'tm' else 'tm'

    if start_at:
        conditions.append(f"{mission_alias}.submission_due_at >= ?")
        params.append(start_at)
    if end_at:
        conditions.append(f"{mission_alias}.start_at <= ?")
        params.append(end_at)
    if experiment_key:
        conditions.append(f"{mission_alias}.experiment_key = ?")
        params.append(experiment_key)
    if mission_key:
        conditions.append(f"{mission_alias}.mission_key = ?")
        params.append(mission_key)
    if market:
        conditions.append(f"{mission_alias}.market = ?")
        params.append(market)

    return (' WHERE ' + ' AND '.join(conditions)) if conditions else '', params


def fetch_challenge_export_rows(
    filename: str,
    *,
    start_at: Optional[str] = None,
    end_at: Optional[str] = None,
    experiment_key: Optional[str] = None,
    challenge_key: Optional[str] = None,
    market: Optional[str] = None,
    limit: int = 100000,
    offset: int = 0,
) -> tuple[list[str], list[dict[str, Any]]]:
    config = CHALLENGE_EXPORTS.get(filename)
    if not config:
        raise ValueError(f'Unsupported challenge export: {filename}')

    alias = config['alias']
    columns = config['columns']
    select_columns = ', '.join(f'{alias}.{column} AS {column}' for column in columns)
    join = f" {config['join']}" if config.get('join') else ''
    where, params = _build_challenge_filters(
        alias,
        start_at=start_at,
        end_at=end_at,
        experiment_key=experiment_key,
        challenge_key=challenge_key,
        market=market,
    )

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT {select_columns}
        FROM {config['table']} {alias}
        {join}
        {where}
        ORDER BY {alias}.id
        LIMIT ? OFFSET ?
        """,
        params + [max(1, min(limit, 100000)), max(0, offset)],
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return columns, rows


def write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def export_challenge_tables(
    output_dir: str | Path,
    *,
    start_at: Optional[str] = None,
    end_at: Optional[str] = None,
    experiment_key: Optional[str] = None,
    challenge_key: Optional[str] = None,
    market: Optional[str] = None,
) -> dict[str, str]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    for filename in CHALLENGE_EXPORTS:
        columns, rows = fetch_challenge_export_rows(
            filename,
            start_at=start_at,
            end_at=end_at,
            experiment_key=experiment_key,
            challenge_key=challenge_key,
            market=market,
        )
        path = target_dir / filename
        write_csv(path, columns, rows)
        written[filename] = str(path)

    return written


def fetch_team_export_rows(
    filename: str,
    *,
    start_at: Optional[str] = None,
    end_at: Optional[str] = None,
    experiment_key: Optional[str] = None,
    mission_key: Optional[str] = None,
    market: Optional[str] = None,
    limit: int = 100000,
    offset: int = 0,
) -> tuple[list[str], list[dict[str, Any]]]:
    config = TEAM_MISSION_EXPORTS.get(filename)
    if not config:
        raise ValueError(f'Unsupported team mission export: {filename}')

    alias = config['alias']
    columns = config['columns']
    select_columns = ', '.join(f'{alias}.{column} AS {column}' for column in columns)
    join = f" {config['join']}" if config.get('join') else ''
    where, params = _build_team_filters(
        alias,
        start_at=start_at,
        end_at=end_at,
        experiment_key=experiment_key,
        mission_key=mission_key,
        market=market,
    )

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT {select_columns}
        FROM {config['table']} {alias}
        {join}
        {where}
        ORDER BY {alias}.id
        LIMIT ? OFFSET ?
        """,
        params + [max(1, min(limit, 100000)), max(0, offset)],
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return columns, rows


def export_team_tables(
    output_dir: str | Path,
    *,
    start_at: Optional[str] = None,
    end_at: Optional[str] = None,
    experiment_key: Optional[str] = None,
    mission_key: Optional[str] = None,
    market: Optional[str] = None,
) -> dict[str, str]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    for filename in TEAM_MISSION_EXPORTS:
        columns, rows = fetch_team_export_rows(
            filename,
            start_at=start_at,
            end_at=end_at,
            experiment_key=experiment_key,
            mission_key=mission_key,
            market=market,
        )
        path = target_dir / filename
        write_csv(path, columns, rows)
        written[filename] = str(path)

    return written
