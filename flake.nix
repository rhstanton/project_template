{
  description = "Reproducible research template dev shell (optional): julia + micromamba + GNU tools, works on macOS and Linux";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        # Julia: nixpkgs `julia` can be unsupported on aarch64-darwin for some pins.
        # Use julia-bin on macOS (prebuilt), julia (from nixpkgs) on Linux.
        juliaPkg =
          if pkgs.stdenv.isDarwin
          then pkgs.julia-bin
          else pkgs.julia;

        basePackages = [
          pkgs.bash
          pkgs.gnumake
          pkgs.coreutils
          pkgs.findutils
          pkgs.gnused
          pkgs.gawk
          pkgs.git
          pkgs.which

          # Project prerequisites (provided by Nix; Makefile/scripts still create .env, etc.)
          juliaPkg
          pkgs.micromamba
        ] ++ pkgs.lib.optionals pkgs.stdenv.isLinux [
          # Linux-only locale archive
          pkgs.glibcLocales
        ];

        baseShellHook = ''
          # Micromamba is available; Makefile uses it for environment setup
          export CONDA=micromamba

          # Keep Julia state local to the repo
          export JULIA_PROJECT="$PWD/env"
          export JULIA_DEPOT_PATH="$PWD/.julia"

          # Locale: avoid bash warnings inside nix shells
          export LANG=C.UTF-8
          export LC_ALL=C.UTF-8
          unset LC_CTYPE LC_NUMERIC LC_TIME LC_COLLATE LC_MONETARY LC_MESSAGES \
                LC_PAPER LC_NAME LC_ADDRESS LC_TELEPHONE LC_MEASUREMENT LC_IDENTIFICATION
        '' + pkgs.lib.optionalString pkgs.stdenv.isLinux ''
          # GPU preference order on Linux (if using JAX or similar)
          export JAX_PLATFORMS="cuda,cpu"
        '';

      in {
        devShells.default = pkgs.mkShell {
          packages = basePackages;
          shellHook = baseShellHook;
        };

        # Optional: Linux GPU extras (use `nix develop .#gpu` on GPU machines)
        devShells.gpu = pkgs.mkShell {
          packages = basePackages ++ pkgs.lib.optionals pkgs.stdenv.isLinux [
            pkgs.cudaPackages.cudatoolkit
            pkgs.cudaPackages.cudnn
          ];
          shellHook = baseShellHook + pkgs.lib.optionalString pkgs.stdenv.isLinux ''
            echo "Nix dev shell: GPU extras enabled (Linux)."
          '';
        };
      }
    );
}
