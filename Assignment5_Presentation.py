# =============================================================================
# Assignment 5: Hotter Planet -> Wilder Storms
# Builds an HTML presentation matching Assignment4.html format.
# Interactive Plotly charts are embedded as iframes from the same html/ folder.
# All 5 chart files must already exist in html/ (run Assignment5_Analysis.py first).
# =============================================================================

from pathlib import Path

HTML_DIR = Path(__file__).parent / "html"
HTML_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = HTML_DIR / "Assignment5.html"

# Chart files produced by Assignment5_Analysis.py -- must exist in html/
CHART_FILES = {
    "temp":  "A5_01_temperature_trend.html",
    "hurr":  "A5_02_hurricane_trends.html",
    "typh":  "A5_03_typhoon_trends.html",
    "torna": "A5_04_tornado_trends.html",
    "corr":  "A5_05_correlation_summary.html",
}

# Verify all charts exist before building presentation
missing = [f for f in CHART_FILES.values() if not (HTML_DIR / f).exists()]
if missing:
    raise FileNotFoundError(
        f"Missing chart files (run Assignment5_Analysis.py first): {missing}"
    )

# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hotter Planet, Wilder Storms &#8212; Assignment 5</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .header {{
            background: #2c3e50;
            color: white;
            padding: 40px 40px;
            border-bottom: 3px solid #34495e;
        }}

        .header h1 {{
            font-size: 2.2em;
            margin-bottom: 12px;
            font-weight: 600;
        }}

        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.95;
            margin-bottom: 15px;
        }}

        .header .meta {{
            font-size: 0.9em;
            opacity: 0.85;
            border-top: 1px solid rgba(255,255,255,0.3);
            padding-top: 12px;
            margin-top: 12px;
        }}

        .intro {{
            padding: 35px 40px;
            background: #fafafa;
            border-bottom: 1px solid #e0e0e0;
            text-align: justify;
        }}

        .intro h2 {{
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.5em;
        }}

        .intro p {{
            font-size: 1.05em;
            color: #555;
            margin-bottom: 12px;
        }}

        .key-finding {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 4px;
            margin: 20px 0;
        }}

        .key-finding h3 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.2em;
            font-weight: 600;
        }}

        .key-finding .stat {{
            font-size: 1.3em;
            font-weight: 600;
            color: #2c3e50;
            margin: 10px 0;
        }}

        .key-finding p {{
            color: #34495E;
            margin: 8px 0;
        }}

        .visualization {{
            padding: 40px 40px;
            border-bottom: 1px solid #e0e0e0;
        }}

        .visualization:last-child {{
            border-bottom: none;
        }}

        .visualization h2 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.6em;
        }}

        .visualization .chart-type {{
            display: inline-block;
            background: #34495e;
            color: white;
            padding: 4px 12px;
            border-radius: 3px;
            font-size: 0.85em;
            margin-bottom: 15px;
            font-weight: 500;
        }}

        .visualization .interactive-hint {{
            display: block;
            font-size: 0.85em;
            color: #888;
            font-style: italic;
            margin-top: 6px;
            margin-bottom: 4px;
        }}

        .visualization .description {{
            margin: 20px 0;
            color: #555;
            text-align: justify;
        }}

        .visualization .description h3 {{
            color: #2c3e50;
            margin-bottom: 10px;
            margin-top: 15px;
            font-size: 1.1em;
        }}

        .visualization .description p {{
            color: #555;
            margin-bottom: 10px;
        }}

        .visualization .description ul {{
            margin-left: 20px;
            color: #555;
        }}

        .visualization .description ul li {{
            margin: 5px 0;
        }}

        .visualization iframe {{
            width: 100%;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-top: 15px;
            display: block;
        }}

        .methodology {{
            padding: 35px 40px;
            background: #f8f9fa;
            text-align: justify;
        }}

        .conclusion {{
            padding: 35px 40px;
            border-bottom: 1px solid #e0e0e0;
            text-align: justify;
        }}

        .conclusion h2 {{
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.5em;
        }}

        .conclusion p {{
            color: #555;
            margin-bottom: 12px;
        }}

        .methodology h2 {{
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.5em;
        }}

        .methodology h3 {{
            color: #34495e;
            margin-top: 20px;
            margin-bottom: 10px;
            font-size: 1.2em;
        }}

        .methodology p, .methodology ul {{
            color: #555;
            margin-bottom: 10px;
        }}

        .methodology ul {{
            margin-left: 25px;
        }}

        .methodology ul li {{
            margin: 6px 0;
        }}

        .footer {{
            padding: 25px 40px;
            background: #2c3e50;
            color: white;
            text-align: center;
        }}

        .footer p {{
            opacity: 0.9;
            font-size: 0.9em;
        }}

        .rubric-note {{
            margin-top: 15px;
            padding: 12px 16px;
            border-top: 1px solid #e0e0e0;
            background: #f8f9fa;
            border-radius: 0 0 4px 4px;
        }}

        .rubric-note strong {{
            color: #2c3e50;
        }}

        .rubric-note p {{
            color: #666;
            font-size: 0.95em;
        }}

        .story-focus {{
            padding: 18px 20px;
            border-left: 4px solid #34495e;
            background: #f8f9fa;
            border-radius: 0 4px 4px 0;
            margin: 20px 0;
        }}

        .story-focus h3 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}

        .story-focus p {{
            color: #2c3e50;
            font-size: 0.97em;
            margin-bottom: 8px;
        }}

        .story-focus ul {{
            margin-left: 20px;
            color: #2c3e50;
            font-size: 0.97em;
        }}

        .story-focus ul li {{
            margin: 4px 0;
        }}

        .storm-photo {{
            margin: 15px 0;
            text-align: center;
        }}

        .storm-photo img {{
            max-width: 100%;
            max-height: 360px;
            border-radius: 4px;
            border: 1px solid #ddd;
            display: block;
            margin: 0 auto;
        }}

        .storm-photo figcaption {{
            font-size: 0.82em;
            color: #777;
            margin-top: 6px;
            font-style: italic;
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}

            .header, .intro, .visualization, .methodology, .footer {{
                padding: 20px;
            }}

            .header h1 {{
                font-size: 1.6em;
            }}

            .visualization iframe {{
                height: 500px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">

        <!-- Header -->
        <div class="header">
            <h1>Hotter Planet, Wilder Storms</h1>
            <div class="subtitle">Temperature and Storm Activity Correlations: Atlantic Hurricanes, Western Pacific Typhoons, and U.S. Tornadoes (2000&ndash;2024)</div>
            <div class="meta">
                Data Sources: NASA GISTEMP v4 &nbsp;|&nbsp; NOAA IBTrACS v4r01 &nbsp;|&nbsp; NOAA SPC Tornado Database &nbsp;|&nbsp; Period: 2000&ndash;2024 &nbsp;|&nbsp; Alinzon Simon
            </div>
        </div>

        <!-- Introduction -->
        <div class="intro">
            <h2>Is a Hotter Planet Making Storms Worse?</h2>
            <p>
                Think about the last time you heard a news alert about a monster hurricane, a deadly
                tornado outbreak, or a typhoon wiping out a coastline. Those headlines seem to keep
                getting bigger. But is that actually true  or does it just feel that way?
            </p>
            <p>
                Here&rsquo;s the basic science: storms run on heat. A hurricane is essentially a giant
                machine that sucks energy out of warm ocean water and turns it into wind and rain.
                The warmer the ocean, the more fuel the storm has. The same goes for tornadoes 
                they form when hot, humid air near the ground slams into a cold front, creating the
                spinning instability that can tear a house apart in seconds.
                <em>If the planet keeps getting hotter, that&rsquo;s more raw energy available for storms to feed on.</em>
            </p>
            <p>
                So what does the data actually say? We pulled 25 years of records from NASA and NOAA
                 the same agencies that track global temperature, hurricane paths, and every
                tornado that touches down in the U.S.  and built five interactive charts to find out.
                Start with Chart&nbsp;1 to see just how much the temperature has already climbed,
                then follow the story through hurricanes, typhoons, tornadoes, and finally a
                side-by-side comparison of all three.
            </p>

            <!-- Story Development Focus -->
            <div class="story-focus">
                <h3>Story Development Focus</h3>
                <p>Two focus points shaped how this story was built:</p>
                <ul>
                    <li><strong>Visual Selection Framework</strong>  Each chart type matches what its
                    question actually needs. A bar chart with a rolling mean is the clearest way to show
                    a temperature trend over time. Dual-axis bar&nbsp;+ line charts let ACE (total seasonal
                    energy) and storm count share one view without distortion. Grouped bars separate
                    all tornadoes from violent ones without hiding either. A scatter grid is the only format
                    that shows the correlation between temperature and four different storm metrics at once.</li>
                    <li><strong>Story Framework</strong>  The five charts tell a connected story: establish
                    the warming signal (Chart&nbsp;1), then test it against each storm type (Charts&nbsp;2&ndash;4),
                    then summarize the statistical evidence (Chart&nbsp;5). Each chart assumes you&rsquo;ve seen the
                    one before it, so the narrative builds rather than repeating itself.</li>
                </ul>
                <p>
                    <strong>Audience:</strong> Earth science students and general readers who want to
                    understand the data behind climate and extreme weather headlines.
                </p>
                <p>
                    <strong>Interactivity:</strong> All five charts are interactive Plotly figures 
                    hover over any data point for exact values, click legend entries to show or hide series,
                    and use the toolbar to zoom or pan.
                </p>
            </div>

            <!-- Key Finding Box -->
            <div class="key-finding">
                <h3>Primary Findings</h3>
                <div class="stat">+1.28&deg;C in 2024  Up +0.89&deg;C Since 2000</div>
                <p>Global temperature has risen sharply over the 25-year study window. Key correlation results:</p>
                <ul style="margin-left: 20px; margin-top: 10px; color: #555;">
                    <li>Atlantic Cat&nbsp;4/5 hurricanes: r = +0.27 (positive trend consistent with warm-ocean intensification physics)</li>
                    <li>Atlantic ACE: r = +0.17 (positive trend across the period)</li>
                    <li>U.S. significant (EF2+) tornadoes: r = +0.09 (positive direction, high natural variability)</li>
                    <li>Western Pacific ACE: r = &minus;0.18 (masked by El Ni&ntilde;o / La Ni&ntilde;a oscillation)</li>
                    <li>All Atlantic and tornado correlations trend in the direction predicted by climate physics</li>
                </ul>
            </div>
        </div>

        <!-- Visualization 1: Temperature Trend -->
        <div class="visualization">
            <h2>Visualization 1: The Warming Signal</h2>
            <span class="chart-type">Bar Chart  Annual Temperature Anomaly + 5-Year Rolling Mean</span>
            <p class="interactive-hint">&#9432; Interactive Plotly chart  hover data points for values, click legend items to show/hide series, zoom and pan with the toolbar.</p>

            <iframe src="{CHART_FILES['temp']}" height="520" frameborder="0" scrolling="no"></iframe>

            <div class="description">
                <h3>What you&rsquo;re looking at</h3>
                <p>
                    Each orange bar represents one year. Its height shows how much warmer
                    that year was compared to the average temperature from 1951 to 1980 
                    the reference period scientists use as the &ldquo;normal&rdquo; baseline.
                    A bar reaching 0.6 means that year was 0.6&deg;C warmer than normal.
                    That might sound small, but across the entire planet, it&rsquo;s enormous.
                </p>
                <p>
                    The smooth black line is a 5-year rolling average  it irons out
                    the year-to-year ups and downs so you can see the bigger trend. Notice
                    how it climbs steadily from left to right, without ever dipping back down.
                    <strong>2024 hit +1.28&deg;C</strong>  the highest ever recorded,
                    and nearly a full degree higher than where the chart starts in 2000.
                </p>
                <p>
                    This chart sets the stage for everything that follows. Before asking
                    whether storms are getting worse, you need to see just how much the
                    thermometer has already moved. Every single year in this 25-year window
                    was above the baseline  not one blue bar in sight.
                </p>
                <div class="rubric-note">
                    <p>
                        <strong>Why this chart type:</strong> A bar chart is the clearest
                        way to show one number per year. Using color to signal &ldquo;above
                        or below normal&rdquo; lets you read the direction at a glance without
                        looking at any numbers. The rolling average line layered on top shows
                        the long-term climb without hiding the year-to-year variation.
                    </p>
                    <p>
                        <strong>Data source:</strong> NASA GISTEMP v4  the same dataset
                        NASA uses in its annual global temperature reports. The zero line
                        is the 1951&ndash;1980 average, unchanged.
                    </p>
                </div>
            </div>
        </div>

        <!-- Visualization 2: Atlantic Hurricanes -->
        <div class="visualization">
            <h2>Visualization 2: Atlantic Hurricane Activity</h2>
            <span class="chart-type">Dual-Axis Bar + Line Chart  ACE and Category 4/5 Count</span>
            <p class="interactive-hint">&#9432; Interactive Plotly chart  hover data points for values, click legend items to show/hide series, zoom and pan with the toolbar.</p>

            <iframe src="{CHART_FILES['hurr']}" height="540" frameborder="0" scrolling="no"></iframe>

            <figure class="storm-photo">
                <img src="https://upload.wikimedia.org/wikipedia/commons/a/a4/Hurricane_Katrina_August_28_2005_NASA.jpg"
                     alt="NASA satellite image of Hurricane Katrina over the Gulf of Mexico on August 28, 2005"
                     onerror="this.parentElement.style.display='none'">
                <figcaption>Hurricane Katrina, August 28, 2005  NASA Terra satellite (MODIS). Category&nbsp;5 at peak intensity, winds of 160&nbsp;mph over the Gulf of Mexico. Credit: Jeff Schmaltz, NASA/GSFC  <em>Public domain</em></figcaption>
            </figure>

            <div class="description">
                <h3>What you&rsquo;re looking at</h3>
                <p>
                    The blue bars show the total <strong>power</strong> of each Atlantic hurricane season.
                    Scientists measure this with a score called ACE  think of it as a running
                    total of how strong every storm was, for how long. A season with lots of strong
                    storms gets a high ACE score; a quiet season gets a low one.
                </p>
                <p>
                    The orange line tracks how many <strong>Category&nbsp;4 and 5 hurricanes</strong>
                    formed each year  the most dangerous storms, with winds above 130&nbsp;mph
                    that can flatten buildings. The teal dotted line shows the total number of named
                    storms (everything from a tropical storm up to a Category&nbsp;5).
                </p>
                <p>
                    <strong>What happened in those labeled years?</strong> 2005 was the year of
                    Hurricane Katrina, which killed over 1,800 people and flooded New Orleans.
                    2017 brought Harvey, Irma, and Maria in quick succession  three
                    Category&nbsp;4+ storms hitting in a single season. 2020 broke the record for
                    most named storms ever (30). 2024 saw Helene and Milton strike within weeks
                    of each other.
                </p>
                <p>
                    <strong>Does warming make it worse?</strong> The data trend says yes, but only
                    weakly so far: in warmer years, there tend to be slightly more Cat&nbsp;4/5 storms
                    (r&nbsp;=&nbsp;+0.27). That&rsquo;s a real positive trend, but with only 25 years
                    of data and natural ups and downs from year to year, it&rsquo;s not yet strong
                    enough to rule out chance. Think of it as a warning signal, not a confirmed fact 
                    more data over time will make the picture clearer.
                </p>
                <div class="rubric-note">
                    <p>
                        <strong>Why this chart type:</strong> Two different measurements  total
                        season power (ACE) and storm count  are shown together using two y-axes.
                        The bars handle the big up-and-down swings in energy; the line shows whether
                        the most dangerous storms are becoming more frequent. Both axes share the same
                        time scale so patterns line up visually.
                    </p>
                    <p>
                        <strong>Data source:</strong> NOAA IBTrACS  the international database
                        that collects tropical cyclone records from weather agencies around the world.
                        Only Atlantic basin storms are included here.
                    </p>
                </div>
            </div>
        </div>

        <!-- Visualization 3: Western Pacific Typhoons -->
        <div class="visualization">
            <h2>Visualization 3: Western Pacific Typhoon Activity</h2>
            <span class="chart-type">Dual-Axis Bar + Line Chart  ACE and Peak Season Wind Speed</span>
            <p class="interactive-hint">&#9432; Interactive Plotly chart  hover data points for values, click legend items to show/hide series, zoom and pan with the toolbar.</p>

            <iframe src="{CHART_FILES['typh']}" height="540" frameborder="0" scrolling="no"></iframe>

            <figure class="storm-photo">
                <img src="https://upload.wikimedia.org/wikipedia/commons/8/8f/Haiyan_11082013_navy_img.jpg"
                     alt="US Navy satellite image of Super Typhoon Haiyan on November 8, 2013"
                     onerror="this.parentElement.style.display='none'">
                <figcaption>Super Typhoon Haiyan, November 8, 2013  Joint Typhoon Warning Center (JTWC), U.S. Navy. Winds of 195&nbsp;mph at landfall in the Philippines. Credit: JTWC  <em>Public domain</em></figcaption>
            </figure>

            <div class="description">
                <h3>What you&rsquo;re looking at</h3>
                <p>
                    Typhoons are the Pacific Ocean&rsquo;s version of hurricanes  same storm,
                    different name. The blue bars show the total seasonal power (ACE score) in the
                    Western Pacific each year. The orange line tracks the <strong>fastest wind
                    speed</strong> recorded anywhere in the basin that season, measured in knots
                    (1 knot &asymp; 1.15 mph). The teal dotted line counts named typhoons per season.
                    The dashed dark-red line shows the long-term trend in peak wind speeds.
                </p>
                <p>
                    <strong>The 2013 spike:</strong> That sharp jump in the orange line is
                    Super Typhoon Haiyan, which hit the Philippines with winds of 170&nbsp;knots
                    (195&nbsp;mph)  the strongest tropical cyclone ever recorded at landfall.
                    It killed over 6,000 people and displaced 4 million more.
                </p>
                <p>
                    <strong>Why doesn&rsquo;t warming show up as clearly here?</strong> The Western
                    Pacific is heavily influenced by El Ni&ntilde;o and La Ni&ntilde;a  a natural
                    ocean temperature cycle that supercharges or suppresses typhoon activity on its
                    own schedule, separate from long-term climate change. It&rsquo;s like trying to
                    hear a quiet song playing in a room where someone keeps turning the volume up and
                    down. The warming signal (r&nbsp;=&nbsp;&minus;0.18) is nearly flat over this
                    25-year window because El Ni&ntilde;o noise drowns it out.
                </p>
                <div class="rubric-note">
                    <p>
                        <strong>Why this chart type:</strong> Same two-axis layout as Visualization&nbsp;2.
                        The bars show the season&rsquo;s total energy; the line shows how extreme the
                        single worst storm got. Plotting them together reveals years like 2008 or 2010
                        where there was a lot of total activity but no record-breaker  and years
                        like 2013 where one storm dominated everything.
                    </p>
                    <p>
                        <strong>Data source:</strong> NOAA IBTrACS Western Pacific basin records.
                        Wind speeds are stored in knots as reported by national weather agencies.
                    </p>
                </div>
            </div>
        </div>

        <!-- Visualization 4: U.S. Tornadoes -->
        <div class="visualization">
            <h2>Visualization 4: U.S. Tornado Trends</h2>
            <span class="chart-type">Overlaid Bar Chart  All Tornadoes vs. Significant (EF2+)</span>
            <p class="interactive-hint">&#9432; Interactive Plotly chart  hover data points for values, click legend items to show/hide series, zoom and pan with the toolbar.</p>

            <iframe src="{CHART_FILES['torna']}" height="540" frameborder="0" scrolling="no"></iframe>

            <figure class="storm-photo">
                <img src="https://upload.wikimedia.org/wikipedia/commons/8/8b/Tornado%2C_Cordell%2C_Oklahoma_1981_-_NOAA.jpg"
                     alt="NOAA photograph of a tornado near Cordell, Oklahoma on May 22, 1981"
                     onerror="this.parentElement.style.display='none'">
                <figcaption>Tornado near Cordell, Oklahoma, May 22, 1981  NOAA National Severe Storms Laboratory. Credit: NOAA Photo Library, NSSL Collection  <em>Public domain</em></figcaption>
            </figure>

            <div class="description">
                <h3>What you&rsquo;re looking at</h3>
                <p>
                    Every year has two overlapping bars. The light-blue bar behind shows
                    <strong>all tornadoes</strong> that touched down in the U.S. that year 
                    from small EF0 twisters that snap tree branches to EF5 monsters that erase towns.
                    The orange bar in front shows only <strong>significant tornadoes (EF2 or stronger)</strong>
                     storms powerful enough to destroy a well-built house. The orange bar is always
                    shorter because EF2+ are a subset of the total. The dashed line shows the slow
                    upward trend in EF2+ counts over time.
                </p>
                <p>
                    <strong>What the labeled years mean:</strong>
                </p>
                <ul>
                    <li><strong>2008</strong>  the deadliest tornado year of the period, with a
                    record number of fatalities across multiple outbreaks.</li>
                    <li><strong>2011</strong>  the 2011 Super Outbreak. On April 27 alone,
                    355 tornadoes touched down in a single 24-hour period, killing 324 people.
                    It remains the largest tornado outbreak in recorded history.</li>
                    <li><strong>2019</strong>  the U.S. experienced tornadoes on a record
                    number of consecutive days, with activity stretching nearly the entire spring.</li>
                    <li><strong>2024</strong>  a record 1,791 tornadoes were reported,
                    the highest single-year total in the dataset.</li>
                </ul>
                <p>
                    <strong>Does warming make tornadoes worse?</strong> The data shows a slight
                    upward lean in EF2+ counts over time, and the direction matches what climate
                    science predicts: warmer, more humid air creates more explosive storm conditions.
                    But tornadoes are chaotic by nature  a single outbreak like 2011 can
                    swing a whole year&rsquo;s number off the chart. With 25 years of data, the
                    warming signal is real but too small to separate from natural noise yet.
                </p>
                <div class="rubric-note">
                    <p>
                        <strong>Why this chart type:</strong> Overlaying the bars (rather than grouping
                        side-by-side or stacking them) shows both the total count and the deadly-storm
                        count in the same bar width. Because EF2+ is always smaller than the total,
                        the orange bar always fits inside the blue one  making it easy to see
                        what fraction of each year&rsquo;s tornadoes were truly dangerous.
                    </p>
                    <p>
                        <strong>Data source:</strong> NOAA Storm Prediction Center tornado database,
                        2000&ndash;2024. EF2+ = Enhanced Fujita scale magnitude 2 or higher.
                        All 50 states included.
                    </p>
                </div>
            </div>
        </div>

        <!-- Visualization 5: Correlation Summary -->
        <div class="visualization">
            <h2>Visualization 5: The Full Picture  Temperature vs. Storm Metrics</h2>
            <span class="chart-type">Scatter Plot Grid  4 Panels, All Storm Types</span>
            <p class="interactive-hint">&#9432; Interactive Plotly chart  hover data points for values, click legend items to show/hide series, zoom and pan with the toolbar.</p>

            <iframe src="{CHART_FILES['corr']}" height="780" frameborder="0" scrolling="no"></iframe>

            <div class="description">
                <h3>How to read it</h3>
                <p>
                    Each panel is a scatter plot. Every <strong>dot is one year</strong>
                    (2000&ndash;2024). Move it to the right and the dot is from a hotter year;
                    move it up and that year had more storm activity. If warming really drives
                    storm intensity, the dots should form a cloud that tilts upward from left
                    to right  and you can draw a rising line through them.
                </p>
                <p>
                    The <strong>dashed line</strong> in each panel is that best-fit trend line.
                    The <strong>r&sup2;</strong> number (yellow box) tells you how tightly the
                    dots follow it  0.00 means no relationship at all; 1.00 would be a
                    perfect straight line. The <strong>p value</strong> tells you whether the
                    pattern could just be random chance  lower is more convincing.
                </p>
                <p>
                    <strong>What the four panels show:</strong> Three of the four panels
                    (Atlantic ACE, Cat&nbsp;4/5 hurricanes, and U.S. tornadoes) tilt upward 
                    warmer years tend to have more intense storms. The Western Pacific panel
                    is flat because El Ni&ntilde;o and La Ni&ntilde;a shuffle Pacific typhoon
                    activity around on their own schedule, drowning out the warming signal.
                </p>
                <p>
                    <strong>Why aren&rsquo;t the numbers bigger?</strong> With only 25 years
                    of data and big natural swings year to year, the trend is real but modest.
                    Think of it like flipping a slightly weighted coin  you&rsquo;d need
                    hundreds of flips to be sure it wasn&rsquo;t just luck. Climate scientists
                    who use 40+ years of data do find stronger and clearer signals, especially
                    for Atlantic hurricanes.
                </p>
                <div class="rubric-note">
                    <p>
                        <strong>Why this chart type:</strong> A scatter grid puts all four
                        storm types on one page so you can compare the patterns side by side.
                        Each panel gets its own y-axis so the different units (ACE, storm count)
                        don&rsquo;t compete with each other. It&rsquo;s the most compact way
                        to show four separate relationships at once.
                    </p>
                    <p>
                        <strong>Data source:</strong> Same NASA and NOAA datasets used in
                        Charts 1&ndash;4, merged into a single 25-row table (one row per year).
                    </p>
                </div>
            </div>
        </div>

        <!-- Conclusion -->
        <div class="conclusion">
            <h2>So What Does the Data Tell Us?</h2>
            <p>
                After 25 years of records from NASA and NOAA, the answer is clear on temperature
                and mixed  but leaning one direction  on storms.
            </p>
            <p>
                <strong>The planet is indisputably warmer.</strong> Every single year since 2000
                has been above the 1951&ndash;1980 average, and 2024 hit +1.28&deg;C 
                the highest ever recorded. That warming is not a trend anymore; it&rsquo;s the
                new normal.
            </p>
            <p>
                <strong>For Atlantic hurricanes, the data points the right direction.</strong>
                In warmer years there tend to be more Category&nbsp;4 and 5 storms
                (r&nbsp;=&nbsp;+0.27), and total season energy trends upward as well. The
                physics matches: warmer ocean water is more fuel. The signal isn&rsquo;t
                overwhelming yet because 25 years is a short window, but it is consistent.
            </p>
            <p>
                <strong>For Western Pacific typhoons, El Ni&ntilde;o dominates the story.</strong>
                The natural year-to-year flip between El Ni&ntilde;o and La Ni&ntilde;a cranks
                typhoon activity up and down so loudly that the long-term warming signal
                (r&nbsp;=&nbsp;&minus;0.18) gets drowned out. That doesn&rsquo;t mean
                typhoons aren&rsquo;t affected; it means we need more years of data to
                separate the two effects.
            </p>
            <p>
                <strong>For U.S. tornadoes, the trend is modest but points the same way.</strong>
                Significant tornadoes (EF2+) trend slightly upward (r&nbsp;=&nbsp;+0.09) in
                warmer years. Tornadoes are chaotic and hard to predict, but they&rsquo;re
                heading in the direction climate physics expects.
            </p>
            <p>
                <strong>The bottom line for a high-school earth science class:</strong>
                A hotter planet loads the dice toward more intense storms. We don&rsquo;t
                see a slam-dunk number in 25 years because nature is noisy. But three of four
                storm metrics trend the way warming physics predicts, the temperature rise
                is unambiguous, and storms like Katrina, Haiyan, and the 2011 Super Outbreak
                are exactly what scientists warned us to expect as the planet heats up.
                The story the data tells is: <em>the signal is real, and it&rsquo;s growing.</em>
            </p>
        </div>

        <!-- Methodology -->
        <div class="methodology">
            <h2>Methodology &amp; Data Sources</h2>

            <h3>Temperature Data</h3>
            <ul>
                <li><strong>NASA GISTEMP v4</strong>  Global mean land-ocean surface temperature anomalies
                    versus the 1951&ndash;1980 baseline. Annual averages (J-D column). Coverage 1880&ndash;2025.
                    File: <code>GLB.Ts+dSST.csv</code></li>
            </ul>

            <h3>Hurricane Data</h3>
            <ul>
                <li><strong>NOAA IBTrACS v4r01  North Atlantic basin</strong>  International Best Track
                    Archive, the world&rsquo;s most complete tropical cyclone record. Filtered to TS and MX
                    nature codes. ACE = &Sigma; V&sup2; / 10,000 per 6-hour record. Category from USA_SSHS.
                    Coverage 1851&ndash;2025. File: <code>ibtracs_NA.csv</code></li>
            </ul>

            <h3>Typhoon Data</h3>
            <ul>
                <li><strong>NOAA IBTrACS v4r01  Western Pacific basin</strong>  Same dataset filtered
                    to BASIN == 'WP'. Coverage 1980&ndash;2026.
                    File: <code>ibtracs_since1980.csv</code></li>
            </ul>

            <h3>Tornado Data</h3>
            <ul>
                <li><strong>NOAA SPC Severe Weather Database</strong>  Official U.S. tornado record with
                    date, state, EF/F-scale magnitude, injuries, fatalities, and path dimensions.
                    Significant = mag &ge; 2 (EF2+). Coverage 1950&ndash;2024.
                    File: <code>spc_tornadoes_1950_2024.csv</code></li>
            </ul>

            <h3>Analysis Period &amp; Statistics</h3>
            <p>
                All datasets aligned to 2000&ndash;2024 (25 years) for a clean overlap covering the modern
                satellite era. Correlations computed using Pearson r (scipy.stats.linregress).
                Statistical significance threshold p &lt; 0.05. Charts built with Python, pandas, numpy,
                scipy, and Plotly.
            </p>

            <h3>Limitations</h3>
            <p>
                A 25-year window is the minimum for detecting long-term climate signals; longer records
                produce stronger statistical significance for Atlantic metrics. ENSO variability
                substantially influences annual Pacific typhoon counts. Tornado EF0&ndash;EF1 detection
                has improved with expanded Doppler radar coverage since the 1990s; EF2+ counts are more
                reliable for trend analysis.
            </p>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>Assignment 5  Data 608: Knowledge and Visual Analytics &nbsp;|&nbsp; NASA GISTEMP &middot; NOAA IBTrACS &middot; NOAA SPC &nbsp;|&nbsp; April 2026</p>
        </div>

    </div>
</body>
</html>
"""

OUTPUT_FILE.write_text(html, encoding="utf-8")
size_kb = OUTPUT_FILE.stat().st_size / 1024
print(f"    Saved: html/Assignment5.html  ({size_kb:.0f} KB)")
print(f"    Open html/Assignment5.html in any browser.")
print(f"    Note: chart iframes require all A5_0*.html files to be in the same html/ folder.")
