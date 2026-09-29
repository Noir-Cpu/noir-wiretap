-- Guards the dd/mm/yy vs dd/mm/yyyy parsing: a mis-parsed year lands far outside the data window.
select match_id, match_date
from {{ ref('stg_informant__matches') }}
where match_date < date '2016-07-01' or match_date > current_date + interval 400 day
