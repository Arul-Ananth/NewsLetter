import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
    plugins: [react()],
    // ADD THIS SECTION:
    server: {
        port: 5173,
        strictPort: true,
        watch: {
            ignored: ["**/newsroom.db", "**/newsroom.db-journal", "**/qdrant_data/**"],
        },
    },
});