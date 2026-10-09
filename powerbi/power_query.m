// =====================================================================
// Euro Area Markets - Power Query (M) scripts
// Power BI Desktop > Transform data > New Source > Blank Query >
// Advanced Editor > paste one query per block below.
//
// Source: CSVs published in this GitHub repo, so the report refreshes
// straight from GitHub (no local files or gateway needed).
// =====================================================================

// ---- Parameter: BaseUrl (Manage Parameters > New, type Text) ---------
// "https://raw.githubusercontent.com/SaurHub007/euro-area-markets-pipeline/main/data/processed/"


// ---- Query: fact_market_monthly --------------------------------------
let
    Source   = Csv.Document(Web.Contents(BaseUrl & "fact_market_monthly.csv"),
                 [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers  = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed    = Table.TransformColumnTypes(Headers, {
                 {"date_key", Int64.Type}, {"series_id", type text},
                 {"value", type number}, {"mom_change", type number},
                 {"yoy_change", type number}, {"mom_pct", type number},
                 {"yoy_pct", type number}}, "en-US")
in
    Typed


// ---- Query: dim_date --------------------------------------------------
let
    Source   = Csv.Document(Web.Contents(BaseUrl & "dim_date.csv"),
                 [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers  = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed    = Table.TransformColumnTypes(Headers, {
                 {"date_key", Int64.Type}, {"month_start", type date},
                 {"year", Int64.Type}, {"quarter", type text},
                 {"month_num", Int64.Type}, {"month_name", type text},
                 {"year_month", type text}}, "en-US")
in
    Typed


// ---- Query: dim_series ------------------------------------------------
let
    Source   = Csv.Document(Web.Contents(BaseUrl & "dim_series.csv"),
                 [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers  = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed    = Table.TransformColumnTypes(Headers, {
                 {"series_id", type text}, {"series_name", type text},
                 {"category", type text}, {"unit", type text},
                 {"ecb_key", type text}, {"is_derived", type logical}}, "en-US")
in
    Typed
