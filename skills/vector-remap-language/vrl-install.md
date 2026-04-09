# Installing the VRL CLI Locally

The `vrl` binary provides a standalone REPL and script runner for VRL — independent of Vector.

> **Note**: There are no pre-built binary releases for the `vrl` CLI. Installation requires the Rust toolchain.

## Prerequisites

- [Rust](https://www.rust-lang.org/tools/install) **1.92 or later** (the project's `rust-toolchain.toml` pins to `1.92`)
- `cargo` (included with Rust)

Install Rust via `rustup`:

```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

## Option 1: Install from crates.io

```sh
cargo install vrl --features cli
```

This installs the latest published version from [crates.io/crates/vrl](https://crates.io/crates/vrl).

To install a specific version:

```sh
cargo install vrl --version 0.31.0 --features cli
```

## Option 2: Build from Source (latest HEAD)

```sh
# Clone the repository
git clone https://github.com/vectordotdev/vrl.git
cd vrl

# Build and install
cargo install --path . --features cli
```

Or just build locally without installing system-wide:

```sh
cargo build --release --features cli
# binary at: ./target/release/vrl
```

## Option 3: Run without Installing

```sh
git clone https://github.com/vectordotdev/vrl.git
cd vrl
cargo run --release --features cli -- --help
cargo run --release --features cli -- '.foo = true'
```

## Verifying the Installation

```sh
vrl --help
vrl --version
```

Expected output:

```
Vector Remap Language CLI

Usage: vrl [OPTIONS] [PROGRAM]
...
```

## Running the REPL

Once installed, launch the interactive REPL:

```sh
vrl
```

Or with a starting event:

```sh
echo '{"message":"hello world"}' > event.json
vrl --input event.json
```

## Feature Flags

The `--features cli` flag is required to build the `vrl` binary. Other relevant flags:

| Flag                       | Description                                                    |
| -------------------------- | -------------------------------------------------------------- |
| `cli`                      | **Required** — enables the CLI binary and REPL                 |
| `stdlib`                   | All standard library functions (included transitively via cli) |
| `enable_env_functions`     | `get_env_var`                                                  |
| `enable_system_functions`  | `get_hostname`, `now`, `get_timezone_name`                     |
| `enable_network_functions` | `dns_lookup`, `reverse_dns`, `http_request`, `community_id`    |
| `enable_crypto_functions`  | `encrypt`, `decrypt`, `encrypt_ip`, `decrypt_ip`               |

All four `enable_*` groups are included in the `default` feature set.

To build with only the base stdlib (no env/system/network/crypto):

```sh
cargo install vrl --no-default-features --features cli,stdlib
```

## Rust Toolchain Compatibility

The project requires Rust **1.92+**. To update rustup:

```sh
rustup update stable
```

Check your current version:

```sh
rustc --version
```

## References

- [VRL GitHub Repository](https://github.com/vectordotdev/vrl)
- [VRL on crates.io](https://crates.io/crates/vrl)
- [VRL docs.rs](https://docs.rs/vrl)
- [Vector Remap Language docs](https://vector.dev/docs/reference/vrl/)
