//! relic-extract — step 2 of scan -> extract -> embed, as one binary.
//!
//!   relic-extract init        write ~/.arra/relic.toml with the defaults, if it is missing
//!   relic-extract config      the [extract] settings in effect (file merged over the defaults)
//!   relic-extract run         relic-scan months -> OUT/<stream>/YYYY-MM.parquet (only what changed)
//!   relic-extract status      per stream: months cut, chunks, distinct texts, newest ts

mod clean;
mod config;
mod extract;
mod json;
mod read;
mod run;

use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(version, about = "relic-scan month files -> per-stream, deduped, chunked parts for embedding")]
struct Cli {
    /// another config (default ~/.arra/relic.toml, or ARRA_CONFIG)
    #[arg(long, global = true)]
    config: Option<String>,
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    /// Write ~/.arra/relic.toml with the defaults (kept if it exists)
    Init,
    /// The settings in effect: the file merged over the defaults
    Config,
    /// Cut the months that changed (or --months) for every stream that is on (or --stream)
    Run {
        /// only these months, comma separated: 2026-09,2026-10
        #[arg(long)]
        months: Option<String>,
        /// only this stream: text | thinking | tools
        #[arg(long)]
        stream: Option<String>,
        /// cut them even if they look fresh
        #[arg(long)]
        force: bool,
        /// the Python reference's cut: every role, no clean step, main-tier sessions (for `just parity`)
        #[arg(long)]
        raw: bool,
    },
    /// Per stream: months, chunks, distinct texts, newest message
    Status,
}

fn fail(e: String) -> ! {
    eprintln!("✗ {e}");
    std::process::exit(1);
}

fn main() {
    let cli = Cli::parse();
    let given = cli.config.as_deref();
    if let Cmd::Init = cli.cmd {
        match config::init(given) {
            Ok((p, made)) => println!("{} {}", if made { "wrote" } else { "kept (already there)" }, p.display()),
            Err(e) => fail(e.to_string()),
        }
        return;
    }
    let mut cfg = config::load(given).unwrap_or_else(|e| fail(e));
    match cli.cmd {
        Cmd::Init => unreachable!(),
        Cmd::Config => {
            println!("# {}{}", cfg.path.display(), if cfg.existed { "" } else { "  (missing: defaults; relic-extract init writes it)" });
            println!("{}", run::pretty(&cfg.v));
        }
        Cmd::Run { months, stream, force, raw } => {
            if raw {
                cfg.raw();
            }
            let t0 = std::time::Instant::now();
            eprintln!("relic-extract: {} -> {} · config {}{}", cfg.source(), cfg.out(), cfg.path.display(),
                      if cfg.existed { "" } else { " (defaults)" });
            let months = months.map(|m| m.split(',').map(|s| s.trim().to_string()).filter(|s| !s.is_empty()).collect());
            let done = run::run(&cfg, months, force, stream.as_deref()).unwrap_or_else(|e| fail(e));
            let (chunks, dropped): (usize, usize) = done.iter().fold((0, 0), |a, d| (a.0 + d.chunks, a.1 + d.dropped));
            eprintln!("{} part(s) cut in {:.1}s · {} chunks · {} messages cleaned out", done.len(), t0.elapsed().as_secs_f64(),
                      extract::num(chunks), extract::num(dropped));
        }
        Cmd::Status => run::status(&cfg),
    }
}
