local servers = {}

servers.lua_ls = {
  filetypes = { "lua" },
  settings = {
    Lua = {
      runtime = { version = "LuaJIT" },
      formatters = { ignoreComments = true },
      signatureHelp = { enabled = true },
      diagnostics = {
        globals = { "vim" },
        disable = { "missing-fields" },
      },
      telemetry = { enabled = false },
    },
  },
}

servers.basedpyright = {
  settings = {
    basedpyright = {
      analysis = { typeCheckingMode = "standard" },
    },
  },
}

servers.nixd = {
  filetypes = { "nix" },
  settings = {
    nixd = {
      nixpkgs = { expr = "import <nixpkgs> {}" },
      options = {
        nixos = {
          expr = '(builtins.getFlake "github:dileep-kishore/nixos-hyprland").nixosConfigurations.tsuki.options',
        },
        home_manger = {
          expr = '(builtins.getFlake "github:dileep-kishore/nixos-hyprland").homeConfigurations."g8k@lap135849".options',
        },
      },
    },
  },
}

servers.gopls = {}

servers.astro = {}

servers.bashls = {}

servers.dockerls = {}

servers.biome = {}

servers.jsonls = {}

servers.harper_ls = {
  filetypes = { "markdown", "gitcommit", "typst", "html", "text" },
}

servers.ltex_plus = {
  filetypes = {
    "bib",
    "org",
    "plaintex",
    "rst",
    "rnoweb",
    "tex",
    "pandoc",
    "quarto",
    "rmd",
    "context",
  },
  settings = {
    checkFrequency = "save",
  },
}

servers.texlab = {
  -- keys = {
  --   { "<Leader>K", "<plug>(vimtex-doc-package)", desc = "Vimtex Docs", silent = true },
  -- },
  settings = {
    texlab = {
      build = {
        executable = "latexmk",
        args = { "-pdf", "-interaction=nonstopmode", "-synctex=1", "%f" },
        onSave = false,
      },
      forwardSearch = {
        executable = "zathura", -- or your PDF viewer
        args = { "--synctex-forward", "%l:1:%f", "%p" },
      },
      chktex = {
        onEdit = false,
        onOpenAndSave = true,
      },
    },
  },
}

servers.marksman = {}

-- NOTE: julials must be installed manually
-- julia --project=~/.julia/environments/nvim-lspconfig -e 'using Pkg; Pkg.add("LanguageServer")'
-- julia --project=~/.julia/environments/nvim-lspconfig -e 'using Pkg; Pkg.update()'
servers.julials = {}

servers.ts_ls = {}

servers.rust_analyzer = {}

servers.svelte = {}

servers.tailwindcss = {}

servers.tinymist = {}

servers.cssls = {}

servers.html = {}

servers.copilot = {}

servers.copilot_ls = {}

return servers
