# ShellCheck Installation

## Package Managers

### Linux

```bash
# Debian/Ubuntu/Mint
sudo apt install shellcheck

# Arch Linux
pacman -S shellcheck
# AUR (dependency-free binary)
yay -S shellcheck-bin

# Gentoo
emerge --ask shellcheck

# EPEL (RHEL/CentOS)
sudo yum -y install epel-release
sudo yum install ShellCheck

# Fedora
dnf install ShellCheck

# FreeBSD
pkg install hs-ShellCheck

# OpenBSD
pkg_add shellcheck

# openSUSE
zypper in ShellCheck
# or OneClickInstall: https://software.opensuse.org/package/ShellCheck

# Solus
eopkg install shellcheck
```

### macOS

```bash
# Homebrew
brew install shellcheck

# MacPorts
sudo port install shellcheck
```

### Windows

```cmd
# Chocolatey
choco install shellcheck

# winget
winget install --id koalaman.shellcheck

# Scoop
scoop install shellcheck
```

### Cross-platform

```bash
# conda-forge
conda install -c conda-forge shellcheck

# Snap Store
snap install --channel=edge shellcheck

# Nix
nix-env -iA nixpkgs.shellcheck

# Flox
flox install shellcheck
```

### Haskell toolchain

```bash
# Cabal (installs to ~/.cabal/bin)
cabal update
cabal install ShellCheck

# Stack (installs to ~/.local/bin)
stack update
stack install ShellCheck
```

## Docker

No local install needed:

```bash
# Stable release
docker run --rm -v "$PWD:/mnt" koalaman/shellcheck:stable myscript.sh

# Specific version
docker run --rm -v "$PWD:/mnt" koalaman/shellcheck:v0.9.0 myscript.sh

# Latest daily build
docker run --rm -v "$PWD:/mnt" koalaman/shellcheck:latest myscript.sh

# Alpine-based image (extendable)
docker run --rm -v "$PWD:/mnt" koalaman/shellcheck-alpine:stable myscript.sh
```

## Pre-compiled Binary

Pre-compiled binaries are statically linked on Linux — no runtime dependencies.

### Direct download (Linux)

```bash
scversion="stable"  # or "v0.9.0", or "latest"
wget -qO- "https://github.com/koalaman/shellcheck/releases/download/${scversion?}/shellcheck-${scversion?}.linux.x86_64.tar.xz" \
  | tar -xJv
sudo cp "shellcheck-${scversion}/shellcheck" /usr/local/bin/
shellcheck --version
```

### Available binaries

| Platform | Architecture | URL                                                                                                       |
| -------- | ------------ | --------------------------------------------------------------------------------------------------------- |
| Linux    | x86_64       | `https://github.com/koalaman/shellcheck/releases/download/stable/shellcheck-stable.linux.x86_64.tar.xz`   |
| Linux    | armv6hf (Pi) | `https://github.com/koalaman/shellcheck/releases/download/stable/shellcheck-stable.linux.armv6hf.tar.xz`  |
| Linux    | aarch64      | `https://github.com/koalaman/shellcheck/releases/download/stable/shellcheck-stable.linux.aarch64.tar.xz`  |
| macOS    | aarch64 (M1) | `https://github.com/koalaman/shellcheck/releases/download/stable/shellcheck-stable.darwin.aarch64.tar.xz` |
| macOS    | x86_64       | `https://github.com/koalaman/shellcheck/releases/download/stable/shellcheck-stable.darwin.x86_64.tar.xz`  |
| Windows  | x86          | `https://github.com/koalaman/shellcheck/releases/download/stable/shellcheck-stable.zip`                   |

> All releases (including `latest` daily builds): <https://github.com/koalaman/shellcheck/releases>

### Extract tarball

```bash
# Requires xz-utils
# Debian/Ubuntu: apt install xz-utils
# RHEL/Fedora:   yum -y install xz

tar -xJf shellcheck-stable.linux.x86_64.tar.xz
sudo mv shellcheck-stable/shellcheck /usr/local/bin/
shellcheck --version
```

## Verify Installation

```bash
shellcheck --version
# ShellCheck - shell script analysis tool
# version: 0.x.x
# ...
```

## CI/CD Pinning

Pin to a specific version in CI to avoid surprise failures from new warning codes:

```yaml
# GitHub Actions
  - name: Install ShellCheck
    run: |
      scversion="v0.9.0"
      wget -qO- "https://github.com/koalaman/shellcheck/releases/download/${scversion}/shellcheck-${scversion}.linux.x86_64.tar.xz" | tar -xJv
      sudo cp "shellcheck-${scversion}/shellcheck" /usr/local/bin/
```

Or use the pre-commit hook approach (see [pre-commit.md](pre-commit.md)) which handles versioning automatically.
