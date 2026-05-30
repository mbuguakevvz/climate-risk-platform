from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from loguru import logger
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.loader import get_all_latest_risk_scores

# ── Colors ──────────────────────────────────────────────
DARK_BG     = colors.HexColor("#0a0f1e")
CARD_BG     = colors.HexColor("#1a1f35")
ACCENT      = colors.HexColor("#00d4ff")
TEXT_WHITE  = colors.HexColor("#ffffff")
TEXT_GREY   = colors.HexColor("#8899aa")
RED         = colors.HexColor("#ff4757")
ORANGE      = colors.HexColor("#ff6b35")
YELLOW      = colors.HexColor("#ffa502")
GREEN       = colors.HexColor("#2ed573")

LEVEL_COLORS = {
    "CRITICAL": RED,
    "HIGH":     ORANGE,
    "MEDIUM":   YELLOW,
    "LOW":      GREEN,
}


def get_level_color(level: str):
    return LEVEL_COLORS.get(level, TEXT_GREY)


def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "ReportTitle",
        fontName="Helvetica-Bold",
        fontSize=24,
        textColor=ACCENT,
        alignment=TA_CENTER,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "ReportSubtitle",
        fontName="Helvetica",
        fontSize=11,
        textColor=TEXT_GREY,
        alignment=TA_CENTER,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "SectionHeader",
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=ACCENT,
        spaceBefore=16,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        "CityName",
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=TEXT_WHITE,
        spaceBefore=10,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        "BodyText2",
        fontName="Helvetica",
        fontSize=9,
        textColor=TEXT_GREY,
        spaceAfter=4,
        leading=14,
    ))
    styles.add(ParagraphStyle(
        "SummaryText",
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#ccddee"),
        spaceAfter=6,
        leading=14,
        leftIndent=10,
    ))
    return styles


def build_header(styles) -> list:
    elements = []
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("🌍 Climate Risk Intelligence Platform", styles["ReportTitle"]))
    elements.append(Paragraph("Global Climate Risk Assessment Report", styles["ReportSubtitle"]))
    elements.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')} · "
        f"Data Sources: Open-Meteo, World Bank · Engine: Rule-Based Risk Scorer",
        styles["ReportSubtitle"]
    ))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    elements.append(Spacer(1, 0.4 * cm))
    return elements


def build_summary_table(df, styles) -> list:
    elements = []
    elements.append(Paragraph("Executive Summary — Global Risk Rankings", styles["SectionHeader"]))

    # KPIs
    critical = len(df[df["risk_level"] == "CRITICAL"])
    high     = len(df[df["risk_level"] == "HIGH"])
    medium   = len(df[df["risk_level"] == "MEDIUM"])
    low      = len(df[df["risk_level"] == "LOW"])
    avg      = df["overall_risk"].mean()
    top_city = df.loc[df["overall_risk"].idxmax(), "city"]

    kpi_data = [
        ["Critical Cities", "High Risk", "Medium Risk", "Low Risk", "Avg Score", "Highest Risk"],
        [str(critical), str(high), str(medium), str(low), f"{avg:.1f}/100", top_city],
    ]

    kpi_table = Table(kpi_data, colWidths=[2.8*cm]*6)
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), CARD_BG),
        ("BACKGROUND",  (0,1), (-1,1), DARK_BG),
        ("TEXTCOLOR",   (0,0), (-1,0), TEXT_GREY),
        ("TEXTCOLOR",   (0,1), (-1,1), TEXT_WHITE),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica"),
        ("FONTNAME",    (0,1), (-1,1), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [CARD_BG, DARK_BG]),
        ("BOX",         (0,0), (-1,-1), 0.5, ACCENT),
        ("INNERGRID",   (0,0), (-1,-1), 0.25, colors.HexColor("#2a3a5c")),
        ("TOPPADDING",  (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 0.5*cm))

    # Main rankings table
    headers = ["Rank", "City", "Country", "Overall", "Level", "Flood", "Drought", "Heatwave", "Air Quality"]
    table_data = [headers]

    sorted_df = df.sort_values("overall_risk", ascending=False).reset_index(drop=True)
    for i, row in sorted_df.iterrows():
        level_color = get_level_color(row["risk_level"])
        table_data.append([
            str(i + 1),
            row["city"],
            row["country"],
            f"{row['overall_risk']:.1f}",
            row["risk_level"],
            f"{row['flood_risk']:.1f}",
            f"{row['drought_risk']:.1f}",
            f"{row['heatwave_risk']:.1f}",
            f"{row['air_quality_risk']:.1f}",
        ])

    col_widths = [1.0*cm, 3.0*cm, 3.2*cm, 1.8*cm, 2.2*cm, 1.6*cm, 1.8*cm, 2.2*cm, 2.4*cm]
    main_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    row_styles = [
        ("BACKGROUND",   (0,0), (-1,0), CARD_BG),
        ("TEXTCOLOR",    (0,0), (-1,0), ACCENT),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 8),
        ("ALIGN",        (0,0), (-1,-1), "CENTER"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("BOX",          (0,0), (-1,-1), 0.5, ACCENT),
        ("INNERGRID",    (0,0), (-1,-1), 0.25, colors.HexColor("#2a3a5c")),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0), (-1,-1), 6),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [DARK_BG, CARD_BG]),
        ("TEXTCOLOR",    (0,1), (-1,-1), TEXT_WHITE),
    ]

    # Color the risk level column per row
    for i, row in sorted_df.iterrows():
        color = get_level_color(row["risk_level"])
        row_styles.append(("TEXTCOLOR", (4, i+1), (4, i+1), color))
        row_styles.append(("FONTNAME",  (4, i+1), (4, i+1), "Helvetica-Bold"))

    main_table.setStyle(TableStyle(row_styles))
    elements.append(main_table)
    return elements


def build_city_cards(df, styles) -> list:
    elements = []
    elements.append(PageBreak())
    elements.append(Paragraph("Detailed City Risk Profiles", styles["SectionHeader"]))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=ACCENT))
    elements.append(Spacer(1, 0.3*cm))

    sorted_df = df.sort_values("overall_risk", ascending=False).reset_index(drop=True)

    for i, row in sorted_df.iterrows():
        level_color = get_level_color(row["risk_level"])

        # City header
        elements.append(Paragraph(
            f"{i+1}. {row['city']}, {row['country']}",
            styles["CityName"]
        ))

        # Risk scores row
        score_data = [[
            f"Overall: {row['overall_risk']:.1f}",
            f"Flood: {row['flood_risk']:.1f}",
            f"Drought: {row['drought_risk']:.1f}",
            f"Heatwave: {row['heatwave_risk']:.1f}",
            f"Air Quality: {row['air_quality_risk']:.1f}",
            row["risk_level"],
        ]]

        score_table = Table(score_data, colWidths=[3.0*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.8*cm, 2.2*cm])
        score_table.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,-1), CARD_BG),
            ("TEXTCOLOR",    (0,0), (-4,-1), TEXT_WHITE),
            ("TEXTCOLOR",    (-1,0), (-1,-1), level_color),
            ("FONTNAME",     (0,0), (-1,-1), "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,-1), 8),
            ("ALIGN",        (0,0), (-1,-1), "CENTER"),
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("BOX",          (0,0), (-1,-1), 0.5, level_color),
            ("INNERGRID",    (0,0), (-1,-1), 0.25, colors.HexColor("#2a3a5c")),
            ("TOPPADDING",   (0,0), (-1,-1), 6),
            ("BOTTOMPADDING",(0,0), (-1,-1), 6),
        ]))
        elements.append(score_table)

        # AI Summary
        elements.append(Paragraph(row["ai_summary"], styles["SummaryText"]))
        elements.append(Spacer(1, 0.2*cm))

        if (i + 1) % 5 == 0 and i < len(sorted_df) - 1:
            elements.append(PageBreak())

    return elements


def build_footer(styles) -> list:
    elements = []
    elements.append(Spacer(1, 0.5*cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=ACCENT))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        "Climate Risk Intelligence Platform · Built by Kevin Mbugua · "
        "github.com/mbuguakevvz · Data: Open-Meteo API, World Bank Climate API",
        ParagraphStyle(
            "Footer",
            fontName="Helvetica",
            fontSize=7,
            textColor=TEXT_GREY,
            alignment=TA_CENTER,
        )
    ))
    return elements


def generate_report(output_path: str = "reports/climate_risk_report.pdf") -> str:
    logger.info("📄 Generating Climate Risk PDF Report...")

    df = get_all_latest_risk_scores()
    if df.empty:
        logger.error("❌ No risk scores found — run the scoring engine first")
        return ""

    os.makedirs("reports", exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=1.5*cm,
        rightMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
        title="Climate Risk Intelligence Report",
        author="Kevin Mbugua — github.com/mbuguakevvz",
    )

    styles = build_styles()
    elements = []

    elements += build_header(styles)
    elements += build_summary_table(df, styles)
    elements += build_city_cards(df, styles)
    elements += build_footer(styles)

    doc.build(elements)
    logger.success(f"✅ Report saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    path = generate_report()
    if path:
        print(f"\n✅ Report ready: {path}")