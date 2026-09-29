select prediction_id
from {{ ref('stg_informant__predictions') }}
where abs(p_home + p_draw + p_away - 1) > 0.01
   or least(p_home, p_draw, p_away) < 0 or greatest(p_home, p_draw, p_away) > 1
   or (book_home is not null and abs(book_home + book_draw + book_away - 1) > 0.01)
