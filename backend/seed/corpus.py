"""Ground-truth reference data: reporter registry + landmark sources.

All citations here are real and correctly formatted. They are the "known good"
universe the verification engine checks against.
"""
from __future__ import annotations

from app.models.enums import SourceType

# (abbreviation, name, min_vol, max_vol, start_year, end_year, courts)
REPORTERS: list[tuple[str, str, int, int | None, int, int | None, str]] = [
    ("U.S.", "United States Reports", 1, 700, 1790, None, "scotus"),
    ("S. Ct.", "Supreme Court Reporter", 1, 200, 1882, None, "scotus"),
    ("L. Ed.", "United States Reports, Lawyers' Edition", 1, 100, 1790, 1956, "scotus"),
    ("L. Ed. 2d", "U.S. Reports, Lawyers' Edition 2d", 1, 220, 1956, None, "scotus"),
    ("F.", "Federal Reporter", 1, 300, 1880, 1924, "fed-circuit,fed-district"),
    ("F.2d", "Federal Reporter, Second Series", 1, 999, 1924, 1993, "fed-circuit"),
    ("F.3d", "Federal Reporter, Third Series", 1, 999, 1993, 2021, "fed-circuit"),
    ("F.4th", "Federal Reporter, Fourth Series", 1, 120, 2021, None, "fed-circuit"),
    ("F. Supp.", "Federal Supplement", 1, 999, 1932, 1998, "fed-district"),
    ("F. Supp. 2d", "Federal Supplement, Second Series", 1, 999, 1998, 2014, "fed-district"),
    ("F. Supp. 3d", "Federal Supplement, Third Series", 1, 700, 2014, None, "fed-district"),
    ("A.2d", "Atlantic Reporter, Second Series", 1, 999, 1938, 2010, "state"),
    ("A.3d", "Atlantic Reporter, Third Series", 1, 300, 2010, None, "state"),
    ("N.E.2d", "North Eastern Reporter, Second Series", 1, 999, 1936, 2004, "state"),
    ("P.3d", "Pacific Reporter, Third Series", 1, 540, 2000, None, "state"),
    ("S.W.3d", "South Western Reporter, Third Series", 1, 690, 1999, None, "state"),
]

# Landmark cases: (title, volume, reporter, page, year, court, summary)
CASES: list[tuple[str, int, str, int, int, str, str]] = [
    ("Brown v. Board of Education", 347, "U.S.", 483, 1954, "scotus",
     "Racial segregation in public schools is unconstitutional."),
    ("Roe v. Wade", 410, "U.S.", 113, 1973, "scotus",
     "Constitutional right to privacy extends to abortion."),
    ("Miranda v. Arizona", 384, "U.S.", 436, 1966, "scotus",
     "Suspects must be informed of rights before custodial interrogation."),
    ("Gideon v. Wainwright", 372, "U.S.", 335, 1963, "scotus",
     "Right to counsel applies to state felony defendants."),
    ("Marbury v. Madison", 5, "U.S.", 137, 1803, "scotus",
     "Established judicial review of legislative acts."),
    ("Obergefell v. Hodges", 576, "U.S.", 644, 2015, "scotus",
     "Same-sex couples have a constitutional right to marry."),
    ("Plessy v. Ferguson", 163, "U.S.", 537, 1896, "scotus",
     "Upheld 'separate but equal'; later overruled by Brown."),
    ("Mapp v. Ohio", 367, "U.S.", 643, 1961, "scotus",
     "Exclusionary rule applies to the states."),
    ("Citizens United v. FEC", 558, "U.S.", 310, 2010, "scotus",
     "Independent political expenditures by corporations are protected speech."),
    ("District of Columbia v. Heller", 554, "U.S.", 570, 2008, "scotus",
     "Second Amendment protects an individual right to keep arms."),
    ("Terry v. Ohio", 392, "U.S.", 1, 1968, "scotus",
     "Police may stop and frisk on reasonable suspicion."),
    ("Chevron U.S.A. Inc. v. NRDC", 467, "U.S.", 837, 1984, "scotus",
     "Courts defer to reasonable agency interpretations of ambiguous statutes."),
    ("Mathews v. Eldridge", 424, "U.S.", 319, 1976, "scotus",
     "Three-factor test for procedural due process."),
    ("New York Times Co. v. Sullivan", 376, "U.S.", 254, 1964, "scotus",
     "Actual-malice standard for defamation of public officials."),
    ("Katz v. United States", 389, "U.S.", 347, 1967, "scotus",
     "Fourth Amendment protects reasonable expectations of privacy."),
    ("Ashcroft v. Iqbal", 556, "U.S.", 662, 2009, "scotus",
     "Pleadings must state a plausible claim for relief."),
    ("Bell Atlantic Corp. v. Twombly", 550, "U.S.", 544, 2007, "scotus",
     "Plausibility pleading standard under Rule 8."),
]

# Statutes: (title, title_number, code, section, summary)
STATUTES: list[tuple[str, int, str, str, str]] = [
    ("Civil action for deprivation of rights", 42, "U.S.C.", "1983",
     "Liability for deprivation of federal rights under color of state law."),
    ("Federal question jurisdiction", 28, "U.S.C.", "1331",
     "District courts have jurisdiction over federal questions."),
    ("Diversity jurisdiction", 28, "U.S.C.", "1332",
     "Jurisdiction over suits between citizens of different states."),
    ("False statements", 18, "U.S.C.", "1001",
     "Criminalizes false statements to the federal government."),
    ("Freedom of Information Act", 5, "U.S.C.", "552",
     "Public access to federal agency records."),
    ("Unlawful employment practices (Title VII)", 42, "U.S.C.", "2000e",
     "Prohibits employment discrimination."),
]

# Regulations: (title, title_number, code, section, summary)
REGULATIONS: list[tuple[str, int, str, str, str]] = [
    ("Sexual harassment guidelines", 29, "C.F.R.", "1604.11",
     "EEOC guidelines on sexual harassment under Title VII."),
    ("Hazardous waste definition", 40, "C.F.R.", "261.3",
     "Defines hazardous waste under RCRA."),
    ("Employment of securities fraud rule 10b-5", 17, "C.F.R.", "240.10b-5",
     "Prohibits fraud in connection with the purchase or sale of securities."),
]


def all_sources() -> list[dict]:
    """Flatten the corpus into source-row dicts (sans embedding)."""
    rows: list[dict] = []
    for title, vol, rep, page, year, court, summary in CASES:
        rows.append(
            dict(
                source_type=SourceType.CASE,
                title=title,
                volume=vol,
                reporter=rep,
                page=page,
                year=year,
                court=court,
                searchable_text=f"{title}. {summary}",
            )
        )
    for title, tnum, code, section, summary in STATUTES:
        rows.append(
            dict(
                source_type=SourceType.STATUTE,
                title=f"{tnum} {code} § {section} — {title}",
                title_number=tnum,
                code=code,
                section=section,
                searchable_text=f"{tnum} {code} {section} {title}. {summary}",
            )
        )
    for title, tnum, code, section, summary in REGULATIONS:
        rows.append(
            dict(
                source_type=SourceType.REGULATION,
                title=f"{tnum} {code} § {section} — {title}",
                title_number=tnum,
                code=code,
                section=section,
                searchable_text=f"{tnum} {code} {section} {title}. {summary}",
            )
        )
    return rows
