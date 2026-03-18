from __future__ import annotations

from urllib.parse import urlparse

import streamlit as st
import streamlit.components.v1 as components

from app.config import AppConfig


def _is_embed_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc.endswith("powerbi.com") and "reportEmbed" in parsed.path


def render_powerbi_section() -> None:
    config = AppConfig()

    if not config.powerbi_embed_url:
        st.info(
            "Add `POWERBI_EMBED_URL` to `.env` or your Streamlit secrets after you "
            "publish the PBIX report to Power BI Service. This section will then embed "
            "the live Power BI report alongside the native dashboard."
        )
        return

    if not _is_embed_url(config.powerbi_embed_url):
        st.markdown(
            """
            <div class="powerbi-hint">
                The current Power BI link is a standard report URL, not a real embed URL.
                Replace it with a <code>reportEmbed</code> or published embed link from Power BI Service.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.link_button("Open Power BI Report", config.powerbi_embed_url, use_container_width=True)
        return

    iframe = f"""
        <iframe
            title="{config.powerbi_title}"
            width="100%"
            height="700"
            src="{config.powerbi_embed_url}"
            frameborder="0"
            allowFullScreen="true">
        </iframe>
    """
    components.html(iframe, height=720)
