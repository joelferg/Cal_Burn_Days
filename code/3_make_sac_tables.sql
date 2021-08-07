CREATE TABLE basin_met (
  date  varchar(10),
  form_date varchar(20),
  time varchar(11),
  meteorologist varchar(30),
  burn_dec_3000 varchar(40),
  am_stab varchar(12),
  wind_spd varchar(13),
  millibar500_ht varchar(14),
  rain varchar(16),
  met_fact varchar(17),
  aq_fact varchar(30),
  alloc_eq varchar(15),
  arb_rev_basin_alloc varchar(18),
  rev_basin_alloc varchar(19)
);

CREATE TABLE district_met (
  date  varchar(10),
  district varchar(15),
  yest_pm25_24hr varchar(5),
  yest_pm25_06 varchar(5),
  red_fact varchar(5),
  proration varchar(20),
  final_alloc varchar(5),
  pm25_06 varchar(5),
  stn varchar(10)
)
