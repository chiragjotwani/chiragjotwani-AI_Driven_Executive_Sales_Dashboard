# AI-Driven Executive Sales Dashboard

## Project Overview
This project combines interactive sales analytics with LLM-generated executive commentary in a single Streamlit application. Business users can explore the dataset through filters and charts, then generate decision-ready insights based on the exact view they are analyzing.

The solution combines:
- **Streamlit** for the web dashboard
- **Python** for data processing and analytics
- **Gemini / OpenAI APIs** for live executive insights
- **Power BI** as an existing reporting asset that can later be embedded into the same app

## Current Structure
- `streamlit_app.py` - Main Streamlit dashboard entrypoint
- `app/` - Modular services for config, data loading, analytics, LLM calls, and Power BI embedding
- `data/raw/sales.csv` - Canonical dataset used by the dashboard
- `notebooks/` - Research notebooks retained for experimentation
- `powerbi/` - Existing Power BI project file

## Features Implemented
- KPI cards for total sales, average order value, orders, and customers
- Interactive filters for date range, region, segment, category, and sub-category
- Native charts for monthly sales, regional performance, category contribution, and top products
- Live LLM insight generation for the current filtered dashboard view
- Optional follow-up question field for chart and trend explanation
- Power BI embed section driven by environment variables for future integration

## Run Locally
1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env`.
3. Add your `OPENAI_API_KEY`.
4. Start the dashboard:

```bash
streamlit run streamlit_app.py
```

## Deploy on Streamlit
1. Push this repository to GitHub.
2. Create a new app in Streamlit Community Cloud.
3. Set the main file path to `streamlit_app.py`.
4. Add the variables from `.streamlit/secrets.toml.example` in the app Secrets panel.
5. Deploy the app.

## Environment Variables
- `OPENAI_API_KEY` - Optional live insight provider
- `OPENAI_MODEL` - Optional model override, defaults to `gpt-4.1-mini`
- `GEMINI_API_KEY` - Optional live insight provider
- `GEMINI_MODEL` - Optional model override, defaults to `gemini-2.5-flash`
- `POWERBI_EMBED_URL` - Optional published Power BI embed URL
- `POWERBI_TITLE` - Optional title for the embedded Power BI report

## LLM Insight Flow
- The dashboard applies the selected filters to the raw sales data.
- Structured metrics and summaries are generated from that filtered slice.
- The LLM receives the analytics payload instead of the full CSV.
- The generated response is shown directly inside the dashboard as an executive summary.

## Power BI Integration
To embed Power BI later:
- Publish `powerbi/Executive_Sales_dashboard.pbix` to Power BI Service.
- Copy the published embed URL.
- Add it to `POWERBI_EMBED_URL` in `.env` or Streamlit deployment secrets.
- The dashboard will render the live report below the native Streamlit visuals.
