import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import './styles/variables.css'
import './styles/transitions.css'
import 'katex/dist/katex.min.css'
import 'highlight.js/styles/github.min.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')
