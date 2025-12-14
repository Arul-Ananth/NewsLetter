// frontend/src-tauri/src/main.rs
#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use tauri::Manager;
// NEW IMPORTS FOR TAURI V2
use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::CommandEvent;

fn main() {
    tauri::Builder::default()
        // REQUIRED: Initialize the shell plugin
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // --- AUTO-START BACKEND (Tauri v2) ---

            // Note: In v2, we use 'app.shell()' instead of 'Command::new_sidecar'
            let (mut rx, _child) = app.shell()
                .sidecar("newsletter-backend")
                .expect("failed to create `newsletter-backend` binary command")
                .spawn()
                .expect("Failed to spawn sidecar");

            // Listen for backend logs
            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) => {
                            if let Ok(s) = String::from_utf8(line) {
                                println!("PY: {}", s);
                            }
                        }
                        CommandEvent::Stderr(line) => {
                            if let Ok(s) = String::from_utf8(line) {
                                println!("PY ERR: {}", s);
                            }
                        }
                        _ => {}
                    }
                }
            });
            // -------------------------------------

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}