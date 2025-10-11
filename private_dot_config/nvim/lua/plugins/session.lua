return {
  "rmagatti/auto-session",
  lazy = false,
  opts = {
    auto_save = true,
    auto_restore = false,
    auto_create = false,
    auto_restore_last_session = false,
    cwd_change_handling = false,
    single_session_mode = false,
    bypass_save_filetypes = { "alpha", "dashboard", "snacks_dashboard" },
    close_unsupported_windows = true,
    git_use_branch_name = true,
    auto_delete_empty_sessions = true,
    session_lens = {
      picker = "snacks",
    },
  },
}
