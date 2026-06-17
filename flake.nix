{
  description = "A terminal-based dashboard for managing cron jobs";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python313;

        textual-autocomplete = python.pkgs.buildPythonPackage {
          pname = "textual-autocomplete";
          version = "4.0.6";
          pyproject = true;

          src = pkgs.fetchPypi {
            pname = "textual_autocomplete";
            version = "4.0.6";
            hash = "sha256-K6Lw12e+RIDsrLPksTDPBzQOAzw1APxCT+2RJdJ6RYY=";
          };

          build-system = [ python.pkgs.hatchling ];
          dependencies = with python.pkgs; [
            textual
            typing-extensions
          ];

          meta = with pkgs.lib; {
            description = "Autocomplete component for Textual TUI apps";
            homepage = "https://github.com/darrenburns/textual-autocomplete";
            license = licenses.mit;
          };
        };

        cronboard = python.pkgs.buildPythonApplication {
          pname = "cronboard";
          version = builtins.elemAt (builtins.match ".*version = \"([^\"]+)\".*" (builtins.readFile ./pyproject.toml)) 0;
          pyproject = true;

          src = ./.;

          build-system = [ python.pkgs.setuptools ];

          dependencies = with python.pkgs; [
            bcrypt
            cron-descriptor
            croniter
            paramiko
            python-crontab
            textual
            tomlkit
            textual-autocomplete
          ];

          meta = with pkgs.lib; {
            description = "A terminal-based dashboard for managing cron jobs";
            homepage = "https://github.com/antoniorodr/cronboard";
            license = licenses.mit;
            mainProgram = "cronboard";
            platforms = platforms.unix;
            maintainers = [ ];
          };
        };
      in
      {
        packages = {
          default = cronboard;
          inherit
            cronboard
            textual-autocomplete
            ;
        };

        apps.default = {
          type = "app";
          program = "${cronboard}/bin/cronboard";
        };

        devShells.default = pkgs.mkShell {
          packages = [
            (python.withPackages (
              ps:
              with ps;
              [
                bcrypt
                cron-descriptor
                croniter
                paramiko
                python-crontab
                textual
                tomlkit
                pytest
                pytest-cov
                pytest-mock
                pytest-asyncio
                textual-dev
              ]
              ++ [
                cron-descriptor
                textual-autocomplete
              ]
            ))
          ];
        };
      }
    );
}
