-- One row per ledger prediction, joined to the result of the same match when it exists.
-- Scores use the ordered outcomes H < D < A:
--   rps      = 1/2 * sum over k=1..2 of (cumulative predicted - cumulative observed)^2
--   log_loss = -ln(probability given to the outcome that happened), probability floored at 1e-15
-- Book columns score the bookmaker probabilities (margin already removed upstream) on the same match.
with p as (
    select * from {{ ref('stg_informant__predictions') }}
),

joined as (
    select
        p.*,
        m.match_id,
        m.result,
        m.season_code
    from p
    left join {{ ref('int_football__matches') }} as m
        on m.league_code = p.league_code
        and m.match_date = p.match_date
        and m.home_team = p.home_team
        and m.away_team = p.away_team
),

scored as (
    select
        *,
        (result is not null) as is_scored,
        case result when 'H' then 1 else 0 end as o_h,
        case result when 'D' then 1 else 0 end as o_d
    from joined
)

select
    *,
    case when is_scored then
        0.5 * (power(p_home - o_h, 2) + power((p_home + p_draw) - (o_h + o_d), 2)) end as rps,
    case when is_scored then
        -ln(greatest(case result when 'H' then p_home when 'D' then p_draw else p_away end, 1e-15)) end as log_loss,
    case when is_scored and book_home is not null then
        0.5 * (power(book_home - o_h, 2) + power((book_home + book_draw) - (o_h + o_d), 2)) end as book_rps,
    case when is_scored and book_home is not null then
        -ln(greatest(case result when 'H' then book_home when 'D' then book_draw else book_away end, 1e-15)) end as book_log_loss,
    -- Re-published predictions must not be counted twice: only the first per match and model is analysed.
    row_number() over (partition by league_code, match_date, home_team, away_team, model_name
                       order by ledger_seq) = 1 as is_first_for_match_model
from scored
