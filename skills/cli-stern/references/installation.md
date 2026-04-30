# stern Installation

## Homebrew (Linux/macOS)

```sh
brew install stern
```

## go install

```sh
go install github.com/stern/stern@latest
```

## asdf (Linux/macOS)

```sh
asdf plugin add stern
asdf install stern latest
```

## Krew (kubectl plugin manager)

```sh
kubectl krew install stern
# Then invoke as: kubectl stern
```

## WinGet (Windows)

```sh
winget install stern.stern
```

## Binary download

Download a pre-built binary from [GitHub Releases](https://github.com/stern/stern/releases).

## Container image

```sh
docker run ghcr.io/stern/stern --version
```

Find available tags at <https://github.com/orgs/stern/packages/container/package/stern>.

## RBAC (running inside Kubernetes Pods)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: stern
rules:
  - apiGroups: ['']
    resources: [pods, pods/log]
    verbs: [get, watch, list]
```

Bind this ClusterRole to the ServiceAccount your Pod uses.
