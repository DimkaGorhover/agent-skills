# Shell Completion

## zsh

```sh
source <(stern --completion=zsh)
```

## bash

```sh
source <(stern --completion=bash)
```

## fish

```sh
stern --completion=fish | source
```

## Krew (kubectl plugin)

```sh
source <(kubectl stern --completion bash)
complete -o default -F __start_stern kubectl stern
```
