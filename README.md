<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Julius Groß · Economics & Data</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta
    name="description"
    content="Personal page of Julius Groß – economics, data, and research."
  />

  <!-- Google Fonts -->
  <link
    href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap"
    rel="stylesheet"
  />

  <style>
    :root {
      --bg: #050816;
      --bg-alt: #0b1020;
      --card: rgba(255, 255, 255, 0.06);
      --accent: #ff7ad9;
      --accent-2: #7cf2ff;
      --text-main: #f9fafb;
      --text-muted: #9ca3af;
      --border-subtle: rgba(255, 255, 255, 0.12);
      --radius-xl: 1.5rem;
      --radius-lg: 1rem;
      --shadow-soft: 0 18px 50px rgba(0, 0, 0, 0.5);
      --max-width: 1040px;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      min-height: 100vh;
      font-family: "Poppins", system-ui, -apple-system, BlinkMacSystemFont,
        "Segoe UI", sans-serif;
      background: radial-gradient(circle at 0% 0%, #1f2937 0, var(--bg) 55%);
      color: var(--text-main);
      -webkit-font-smoothing: antialiased;
    }

    a {
      color: inherit;
      text-decoration: none;
    }

    main {
      max-width: var(--max-width);
      margin: 0 auto;
      padding: 2.5rem 1.5rem 4rem;
      position: relative;
      z-index: 1;
    }

    /* Background blobs */
    .blob {
      position: fixed;
      border-radius: 999px;
      filter: blur(70px);
      opacity: 0.4;
      z-index: 0;
      pointer-events: none;
    }

    .blob-1 {
      width: 360px;
      height: 360px;
      background: #ff7ad9;
      top: -80px;
      right: -80px;
    }

    .blob-2 {
      width: 260px;
      height: 260px;
      background: #7cf2ff;
      bottom: -60px;
      left: -40px;
    }

    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1.5rem;
      margin-bottom: 3rem;
    }

    .logo-mark {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.35rem 0.8rem;
      border-radius: 999px;
      border: 1px solid var(--border-subtle);
      background: rgba(15, 23, 42, 0.8);
      backdrop-filter: blur(14px);
      font-size: 0.8rem;
      color: var(--text-muted);
    }

    .logo-dot {
      width: 9px;
      height: 9px;
      border-radius: 999px;
      background: radial-gradient(circle at 30% 30%, #ffffff, var(--accent));
      box-shadow: 0 0 0 6px rgba(255, 122, 217, 0.25);
    }

    nav {
      display: flex;
      gap: 0.9rem;
      font-size: 0.88rem;
    }

    nav a {
      padding: 0.4rem 0.9rem;
      border-radius: 999px;
      border: 1px solid transparent;
      color: var(--text-muted);
      transition: all 0.2s ease;
      white-space: nowrap;
    }

    nav a:hover {
      border-color: rgba(255, 255, 255, 0.2);
      background: rgba(15, 23, 42, 0.8);
      color: var(--text-main);
    }

    .hero {
      display: grid;
      grid-template-columns: minmax(0, 2.1fr) minmax(0, 1.6fr);
      gap: 2.5rem;
      align-items: center;
      margin-bottom: 3.5rem;
    }

    .badge-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.6rem;
      margin-bottom: 1.4rem;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.25rem 0.8rem;
      border-radius: 999px;
      background: rgba(15, 23, 42, 0.9);
      border: 1px solid var(--border-subtle);
      font-size: 0.75rem;
      color: var(--text-muted);
    }

    .pill span.dot {
      width: 7px;
      height: 7px;
      border-radius: 999px;
      background: var(--accent-2);
    }

    .hero h1 {
      font-size: clamp(2.4rem, 4vw, 3rem);
      line-height: 1.1;
      margin-bottom: 0.6rem;
    }

    .hero h1 span {
      background: linear-gradient(120deg, #ff7ad9, #7cf2ff);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
    }

    .hero-subtitle {
      font-size: 0.98rem;
      color: var(--text-muted);
      margin-bottom: 1.5rem;
      max-width: 32rem;
    }

    .hero-subtitle strong {
      color: #e5e7eb;
      font-weight: 500;
    }

    .hero-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 0.9rem;
      align-items: center;
    }

    .btn-primary,
    .btn-ghost {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.45rem;
      padding: 0.6rem 1.2rem;
      border-radius: 999px;
      font-size: 0.9rem;
      border: 1px solid transparent;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .btn-primary {
      background: linear-gradient(130deg, var(--accent), var(--accent-2));
      color: #020617;
      font-weight: 600;
      box-shadow: 0 10px 28px rgba(15, 23, 42, 0.7);
    }

    .btn-primary:hover {
      transform: translateY(-1px);
      box-shadow: 0 16px 40px rgba(15, 23, 42, 0.9);
    }

    .btn-ghost {
      background: rgba(15, 23, 42, 0.8);
      border-color: var(--border-subtle);
      color: var(--text-muted);
    }

    .btn-ghost:hover {
      background: rgba(15, 23, 42, 1);
      color: var(--text-main);
    }

    .btn-icon {
      font-family: "Fira Code", monospace;
      font-size: 0.88rem;
    }

    .hero-right {
      position: relative;
      padding: 1.2rem;
    }

    .card {
      border-radius: var(--radius-xl);
      background: radial-gradient(circle at 0 0, rgba(124, 242, 255, 0.12), transparent 60%),
        radial-gradient(circle at 100% 100%, rgba(255, 122, 217, 0.18), transparent 60%),
        rgba(15, 23, 42, 0.95);
      border: 1px solid var(--border-subtle);
      box-shadow: var(--shadow-soft);
      padding: 1.6rem 1.7rem;
      position: relative;
      overflow: hidden;
    }

    .card::before {
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(
          120deg,
          rgba(255, 255, 255, 0.08),
          transparent 40%,
          transparent 60%,
          rgba(255, 255, 255, 0.05)
        );
      opacity: 0.24;
      mix-blend-mode: screen;
      pointer-events: none;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.1rem;
      position: relative;
      z-index: 1;
    }

    .card-title {
      font-size: 0.9rem;
      color: var(--text-muted);
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: #22c55e;
      box-shadow: 0 0 0 6px rgba(34, 197, 94, 0.15);
    }

    .tag-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-bottom: 1.2rem;
      position: relative;
      z-index: 1;
    }

    .tag {
      font-size: 0.7rem;
      padding: 0.25rem 0.7rem;
      border-radius: 999px;
      border: 1px dashed rgba(148, 163, 184, 0.7);
      color: #e5e7eb;
      background: rgba(15, 23, 42, 0.8);
    }

    .card-body {
      font-size: 0.82rem;
      color: var(--text-muted);
      position: relative;
      z-index: 1;
      line-height: 1.5;
    }

    .card-body p + p {
      margin-top: 0.35rem;
    }

    .code-block {
      margin-top: 0.9rem;
      padding: 0.7rem 0.8rem;
      border-radius: var(--radius-lg);
      background: rgba(15, 23, 42, 0.98);
      border: 1px solid rgba(51, 65, 85, 0.8);
      font-family: "Fira Code", monospace;
      font-size: 0.78rem;
      color: #e5e7eb;
      white-space: nowrap;
      overflow-x: auto;
    }

    .code-comment {
      color: #6b7280;
    }

    .code-keyword {
      color: #7cf2ff;
    }

    .code-number {
      color: #fbbf24;
    }

    .code-string {
      color: #f97373;
    }

    section {
      margin-bottom: 3rem;
    }

    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 1rem;
      gap: 1rem;
    }

    .section-title {
      font-size: 1.1rem;
      font-weight: 600;
    }

    .section-kicker {
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--text-muted);
    }

    .section-subtitle {
      font-size: 0.88rem;
      color: var(--text-muted);
    }

    .grid-2 {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 1.1rem;
    }

    .item-card {
      background: var(--card);
      border-radius: var(--radius-lg);
      border: 1px solid var(--border-subtle);
      padding: 1rem 1.1rem;
      backdrop-filter: blur(12px);
      position: relative;
      overflow: hidden;
    }

    .item-card h3 {
      font-size: 0.94rem;
      margin-bottom: 0.2rem;
    }

    .item-meta {
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-bottom: 0.5rem;
    }

    .item-body {
      font-size: 0.82rem;
      color: #e5e7eb;
    }

    .pill-small {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      padding: 0.2rem 0.55rem;
      border-radius: 999px;
      border: 1px solid rgba(148, 163, 184, 0.7);
      font-size: 0.7rem;
      color: var(--text-muted);
      margin-top: 0.4rem;
    }

    .pill-small span {
      font-size: 0.8em;
    }

    .list {
      list-style: none;
      font-size: 0.85rem;
      color: var(--text-muted);
    }

    .list li + li {
      margin-top: 0.3rem;
    }

    .highlight {
      color: #e5e7eb;
    }

    footer {
      border-top: 1px solid rgba(31, 41, 55, 0.9);
      padding-top: 1.6rem;
      margin-top: 1rem;
      font-size: 0.8rem;
      color: var(--text-muted);
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: 1rem;
    }

    footer a {
      color: var(--text-muted);
    }

    footer a:hover {
      color: var(--text-main);
    }

    /* Responsive */
    @media (max-width: 900px) {
      header {
        flex-direction: column;
        align-items: flex-start;
      }
      nav {
        flex-wrap: wrap;
      }
      .hero {
        grid-template-columns: minmax(0, 1fr);
      }
      .hero-right {
        order: -1;
      }
    }

    @media (max-width: 640px) {
      main {
        padding-inline: 1.1rem;
      }
      .grid-2 {
        grid-template-columns: minmax(0, 1fr);
      }
      .hero-actions {
        flex-direction: column;
        align-items: flex-start;
      }
    }
  </style>
</head>
<body>
  <div class="blob blob-1"></div>
  <div class="blob blob-2"></div>

  <main>
    <header>
      <div class="logo-mark">
        <span class="logo-dot"></span>
        <span>Julius&nbsp;Groß</span>
      </div>
      <nav>
        <a href="#about">About</a>
        <a href="#research">Research</a>
        <a href="#teaching">Teaching</a>
        <a href="#projects">Projects</a>
        <a href="#contact">Contact</a>
      </nav>
    </header>

    <!-- HERO -->
    <section class="hero" id="top">
      <div>
        <div class="badge-row">
          <div class="pill">
            <span class="dot"></span>
            <span>Economics · Data · Policy</span>
          </div>
          <div class="pill">
            <span>Currently:</span>
            <!-- TODO: adjust affiliation -->
            <strong>PhD Student, University of Cologne</strong>
          </div>
        </div>

        <h1>
          Hi, I’m <span>Julius</span>.<br />
          I like making data tell better stories.
        </h1>

        <p class="hero-subtitle">
          I work at the intersection of <strong>economics</strong>,
          <strong>data science</strong>, and <strong>policy</strong>. I enjoy
          building careful empirical designs, clean code, and visualisations
          that make complex ideas intuitive.
        </p>

        <div class="hero-actions">
          <!-- TODO: point this to your actual CV file -->
          <a class="btn-primary" href="cv.pdf" target="_blank" rel="noopener">
            <span>Download CV</span>
            <span class="btn-icon">↗</span>
          </a>

          <!-- TODO: set GitHub and/or other links -->
          <a
            class="btn-ghost"
            href="https://github.com/JuliusGr01"
            target="_blank"
            rel="noopener"
          >
            <span>GitHub</span>
          </a>
        </div>
      </div>

      <div class="hero-right">
        <div class="card">
          <div class="card-header">
            <div class="card-title">Currently thinking about</div>
            <div class="status-dot"></div>
          </div>
          <div class="tag-row">
            <span class="tag">Trade & global shocks</span>
            <span class="tag">Inequality & beliefs</span>
            <span class="tag">Causal ML</span>
            <span class="tag">Text & survey data</span>
          </div>
          <div class="card-body">
            <p>
              I’m interested in how people form beliefs about the economy and
              how these beliefs shape behaviour and policy preferences.
            </p>
            <p>
              Methodologically, I like combining <span class="highlight"
                >micro data, natural experiments, and flexible ML
                techniques</span
              >
              in transparent research designs.
            </p>

            <div class="code-block">
              <span class="code-comment"># pseudo-code of my brain</span><br />
              <span class="code-keyword">beliefs</span> = model(
              <span class="code-string">"inequality"</span>,
              <span class="code-string">"mobility"</span>,
              <span class="code-string">"fairness"</span> )<br />
              <span class="code-keyword">policy_support</span> =
              f(beliefs, institutions)<br />
              if <span class="code-keyword">data</span>.richness &gt;
              <span class="code-number">0</span>:
              <span class="code-keyword">estimate</span>(policy_support)
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ABOUT -->
    <section id="about">
      <div class="section-header">
        <div>
          <div class="section-kicker">About</div>
          <h2 class="section-title">Who I am in a few lines</h2>
        </div>
        <div class="section-subtitle">
          Econometrics enjoyer, Stata/R/Python trilingual, occasional teacher.
        </div>
      </div>

      <p class="section-subtitle" style="max-width: 48rem; margin-bottom: 1rem;">
        I’m a PhD student in economics working on questions around
        <span class="highlight">climate & environment</span>,
        <span class="highlight">inequality</span>, and
        <span class="highlight">belief formation</span>. Before my PhD, I spent
        time doing research assistance, building forecasting models, and
        experimenting with survey and text data.
      </p>

      <ul class="list">
        <!-- TODO: adapt items to your actual background -->
        <li>
          • Tools I enjoy working with:
          <span class="highlight">Stata, R, Python, Git, VS Code</span>
        </li>
        <li>
          • Methods I like:
          <span class="highlight"
            >causal inference, panel models, time series, ML for policy</span
          >
        </li>
        <li>
          • Outside of work you’ll probably find me
          <span class="highlight">somewhere between a coffee and a train</span
          >.
        </li>
      </ul>
    </section>

    <!-- RESEARCH -->
    <section id="research">
      <div class="section-header">
        <div>
          <div class="section-kicker">Research</div>
          <h2 class="section-title">Projects & ideas</h2>
        </div>
        <div class="section-subtitle">
          Working papers, early-stage ideas, and things I’d like to write down.
        </div>
      </div>

      <div class="grid-2">
        <!-- Example project 1 -->
        <article class="item-card">
          <h3>Neural networks to forecast trade</h3>
          <div class="item-meta">
            with B. Meunier · work in progress
          </div>
          <div class="item-body">
            We explore when flexible predictive models beat classical time series
            methods for forecasting trade flows, and try to understand why
            through careful model diagnostics and structure.
          </div>
          <div class="pill-small">
            <span>Methods:</span> MLS, time series, forecasting
          </div>
        </article>

        <!-- Example project 2 -->
        <article class="item-card">
          <h3>Monetary policy & a polarized labour market</h3>
          <div class="item-meta">with T. Zimmermann · work in progress</div>
          <div class="item-body">
            How does monetary policy affect workers differently across the wage
            distribution? We combine micro labour data with macro shocks to
            trace out heterogeneous transmission channels.
          </div>
          <div class="pill-small">
            <span>Data:</span> micro labour, macro shocks
          </div>
        </article>

        <!-- Placeholder for own PhD work -->
        <article class="item-card">
          <h3>Beliefs about inequality & redistribution</h3>
          <div class="item-meta">PhD thesis project · early stage</div>
          <div class="item-body">
            I study how people perceive the income distribution and mobility in
            their country, how accurate those perceptions are, and how they
            relate to fairness judgements and support for redistribution.
          </div>
          <div class="pill-small">
            <span>Keywords:</span> surveys, beliefs, experimental economics
          </div>
        </article>

        <!-- Another box: open to collaborations -->
        <article class="item-card">
          <h3>Open to collaborations</h3>
          <div class="item-meta">Let’s talk</div>
          <div class="item-body">
            If you’re working on <span class="highlight">trade, climate,
            inequality, or survey/experimental work</span> and think we could
            do something fun together, I’m always happy to chat.
          </div>
          <div class="pill-small">
            <span>Ping me:</span> see contact below
          </div>
        </article>
      </div>
    </section>

    <!-- TEACHING -->
    <section id="teaching">
      <div class="section-header">
        <div>
          <div class="section-kicker">Teaching</div>
          <h2 class="section-title">Courses & supervision</h2>
        </div>
        <div class="section-subtitle">
          I like helping students get from “what is this?” to “oh, that’s neat”.
        </div>
      </div>

      <div class="grid-2">
        <!-- TODO: adapt teaching list -->
        <article class="item-card">
          <h3>Econometrics / Data analysis tutorials</h3>
          <div class="item-meta">University of Cologne · tutor</div>
          <div class="item-body">
            Tutorials and problem sets for undergraduate econometrics, focusing
            on intuition, visualisation, and reproducible code.
          </div>
          <div class="pill-small">
            <span>Software:</span> Stata, R
          </div>
        </article>

        <article class="item-card">
          <h3>Supervision</h3>
          <div class="item-meta">Bachelor / Master theses</div>
          <div class="item-body">
            I’m happy to supervise theses that work with real data and clear
            identification strategies, especially on topics related to
            inequality, beliefs, or climate.
          </div>
          <div class="pill-small">
            <span>Interested?</span> Reach out by email
          </div>
        </article>
      </div>
    </section>

    <!-- PROJECTS / CODE -->
    <section id="projects">
      <div class="section-header">
        <div>
          <div class="section-kicker">Code</div>
          <h2 class="section-title">Things I build</h2>
        </div>
        <div class="section-subtitle">
          Small tools and projects that make data work smoother.
        </div>
      </div>

      <div class="grid-2">
        <!-- TODO: link to real repos -->
        <article class="item-card">
          <h3>Trade forecasting toolbox</h3>
          <div class="item-meta">R / Python · in progress</div>
          <div class="item-body">
            A collection of scripts for estimating and comparing
            forecasting models for trade data (VARs, ARDL, ML baselines).
          </div>
          <div class="pill-small">
            <span>GitHub:</span> coming soon
          </div>
        </article>

        <article class="item-card">
          <h3>Teaching utilities</h3>
          <div class="item-meta">Stata / R snippets</div>
          <div class="item-body">
            Clean templates for problem sets, plotting routines, and
            reproducible project structures used in teaching.
          </div>
          <div class="pill-small">
            <span>Focus:</span> clarity & reproducibility
          </div>
        </article>
      </div>
    </section>

    <!-- CONTACT -->
    <section id="contact">
      <div class="section-header">
        <div>
          <div class="section-kicker">Contact</div>
          <h2 class="section-title">Say hi</h2>
        </div>
        <div class="section-subtitle">
          Conferences, research ideas, or just a coffee recommendation.
        </div>
      </div>

      <div class="item-card" style="max-width: 480px;">
        <div class="item-body">
          <p>
            The easiest way to reach me is by email. I try to respond reasonably
            quickly, especially to students and co-authors.
          </p>

          <ul class="list" style="margin-top: 0.7rem;">
            <!-- TODO: put your real email / links -->
            <li>
              • Email:
              <a href="mailto:your.email@uni-koeln.de" class="highlight"
                >your.email@uni-koeln.de</a
              >
            </li>
            <li>
              • GitHub:
              <a
                href="https://github.com/JuliusGr01"
                target="_blank"
                rel="noopener"
                class="highlight"
                >@JuliusGr01</a
              >
            </li>
            <li>
              • Office / department:
              <span class="highlight">University of Cologne</span>
            </li>
          </ul>
        </div>
      </div>
    </section>

    <footer>
      <div>© <span id="year"></span> Julius Groß</div>
      <div>
        Built with <span class="highlight">plain HTML & CSS</span> · Hosted on
        <a href="https://pages.github.com/" target="_blank" rel="noopener"
          >GitHub Pages</a
        >
      </div>
    </footer>
  </main>

  <script>
    // Set current year in footer
    document.getElementById("year").textContent =
      new Date().getFullYear().toString();
  </script>
</body>
</html>
