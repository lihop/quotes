# SPDX-FileCopyrightText: none
#
# SPDX-License-Identifier: CC0-1.0
let
  hostPkgs = import <nixpkgs> { };
  pkgs = import
    (hostPkgs.fetchFromGitHub {
      owner = "NixOS";
      repo = "nixpkgs";
      rev = "a343533bccc62400e8a9560423486a3b6c11a23b";
      sha256 = "sha256-TofHtnlrOBCxtSZ9nnlsTybDnQXUmQrlIleXF1RQAwQ=";
    })
    { };
in
hostPkgs.mkShell {
  buildInputs = [
    pkgs.cypress
    pkgs.nodejs_20
    pkgs.playwright-driver.browsers
    pkgs.jq
    (pkgs.python3.withPackages (ps: with ps; [
      autopep8
      beautifulsoup4
      fpdf
      html5lib
      lxml
      numpy
      openpyxl
      pandas
      pip
      requests
      sqlite-utils
      tabula-py
    ]))
  ];
  shellHook = ''
    export CYPRESS_INSTALL_BINARY=0
    export CYPRESS_RUN_BINARY=${pkgs.cypress}/bin/Cypress
    export PLAYWRIGHT_BROWSERS_PATH=${pkgs.playwright-driver.browsers}
    export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true
    
    # Use the playwright-driver browsers directly
    export PLAYWRIGHT_LAUNCH_OPTIONS_EXECUTABLE_PATH="${pkgs.playwright-driver.browsers}/chromium-1091/chrome-linux/chrome"

    # Tells pip to put packages into $PIP_PREFIX instead of the usual locations.
    # See https://pip.pypa.io/en/stable/user_guide/#environment-variables.
    export PIP_PREFIX=$(pwd)/_build/pip_packages
    export PYTHONPATH="$PIP_PREFIX/${pkgs.python3.sitePackages}:$PYTHONPATH"
    export PATH="$PIP_PREFIX/bin:$PATH"
    unset SOURCE_DATE_EPOCH
  '';
}
