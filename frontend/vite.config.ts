import { defineConfig } from 'vite';
export default defineConfig({server:{port:5173,proxy:{'/api':{target:'http://127.0.0.1:8004',ws:true},'/health':'http://127.0.0.1:8004','/ws':{target:'ws://127.0.0.1:8004',ws:true},'/media':'http://127.0.0.1:8004'}}});
