class InteractiveBackground {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.points = [];
        this.mouse = { x: -1000, y: -1000 };
        this.spacing = 40;
        this.radius = 150;
        this.strength = 0.3;
        this.baseColor = 'rgba(59, 130, 246, 0.2)';
        
        window.addEventListener('resize', () => this.init());
        document.addEventListener('mousemove', (e) => {
            this.mouse.x = e.clientX;
            this.mouse.y = e.clientY;
        });
        
        this.init();
        this.animate();
    }

    init() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        this.points = [];
        const countX = Math.ceil(this.canvas.width / this.spacing) + 1;
        const countY = Math.ceil(this.canvas.height / this.spacing) + 1;
        for (let x = 0; x < countX; x++) {
            for (let y = 0; y < countY; y++) {
                this.points.push({ baseX: x * this.spacing, baseY: y * this.spacing, x: x * this.spacing, y: y * this.spacing, vx: 0, vy: 0 });
            }
        }
    }

    update() {
        const theme = document.documentElement.getAttribute('data-theme');
        this.baseColor = theme === 'dark' ? 'rgba(59, 130, 246, 0.35)' : 'rgba(37, 99, 235, 0.25)';

        this.points.forEach(p => {
            const dx = this.mouse.x - p.x;
            const dy = this.mouse.y - p.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            
            if (dist < this.radius) {
                const force = (this.radius - dist) / this.radius;
                p.vx += dx * force * 0.035;
                p.vy += dy * force * 0.035;
            }
            
            // Snap back
            p.vx += (p.baseX - p.x) * 0.05;
            p.vy += (p.baseY - p.y) * 0.05;
            
            // Friction
            p.vx *= 0.92;
            p.vy *= 0.92;
            
            p.x += p.vx;
            p.y += p.vy;
        });
    }

    draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.fillStyle = this.baseColor;
        this.ctx.beginPath();
        this.points.forEach(p => {
            this.ctx.moveTo(p.x, p.y);
            this.ctx.arc(p.x, p.y, 1.4, 0, Math.PI * 2);
        });
        this.ctx.fill();
    }

    animate() {
        this.update();
        this.draw();
        requestAnimationFrame(() => this.animate());
    }
}

const translations = {
    en: {
        title: "Generate QR",
        subtitle: "Create custom QR codes with your brand logo in seconds.",
        label_text: "QR Content",
        label_fg: "Color",
        label_bg: "Background",
        label_shape: "Shape Style",
        opt_square: "Square",
        opt_rounded: "Rounded",
        opt_circle: "Circle",
        label_logo: "Logo (Drop here)",
        upload_text: "Choose or Drop image...",
        label_size: "Logo Size (max 15%)",
        placeholder: "Waiting for content...",
        rights: "All Rights Reserved."
    },
    es: {
        title: "Generar QR",
        subtitle: "Crea códigos QR personalizados con tu logo en segundos.",
        label_text: "Contenido del QR",
        label_fg: "Color",
        label_bg: "Fondo",
        label_shape: "Estilo de Forma",
        opt_square: "Cuadrado",
        opt_rounded: "Redondeado",
        opt_circle: "Círculo",
        label_logo: "Logo (Suelta aquí)",
        upload_text: "Elige o suelta imagen...",
        label_size: "Tamaño (máx 15%)",
        placeholder: "Esperando contenido...",
        rights: "Todos los derechos reservados."
    }
};

document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('bg-canvas');
    if (canvas) new InteractiveBackground(canvas);

    const elements = {
        qrimg: document.getElementById('qrcodeimg'),
        qrtxt: document.getElementById('qrtext'),
        logoInput: document.getElementById('logo'),
        logoScale: document.getElementById('logo_scale'),
        logoScaleValue: document.getElementById('logo-scale-value'),
        qrPlaceholder: document.getElementById('qr-placeholder'),
        themeToggle: document.getElementById('theme-toggle'),
        headerLogo: document.getElementById('header-logo'),
        langSelect: document.getElementById('lang-select'),
        uploadText: document.getElementById('t-upload-text'),
        fgColor: document.getElementById('fg_color'),
        bgColor: document.getElementById('bg_color'),
        dropZone: document.getElementById('logo-drop-zone')
    };

    let currentTheme = localStorage.getItem('theme') || 'dark';
    let currentLang = localStorage.getItem('lang') || 'en';

    // Set defaults if not present
    if (!localStorage.getItem('theme')) localStorage.setItem('theme', 'dark');
    if (!localStorage.getItem('lang')) localStorage.setItem('lang', 'en');

    document.documentElement.setAttribute('data-theme', currentTheme);
    elements.langSelect.value = currentLang;
    updateYear();
    applyLocalization(currentLang);
    updateThemeUI(currentTheme);

    // Initial Load if values exist
    if (elements.qrtxt.value) fetchcode();

    // Event Listeners
    elements.themeToggle.addEventListener('click', toggleTheme);
    elements.langSelect.addEventListener('change', (e) => {
        currentLang = e.target.value;
        localStorage.setItem('lang', currentLang);
        applyLocalization(currentLang);
    });

    // QR Logic Listeners
    [elements.qrtxt, elements.fgColor, elements.bgColor].forEach(el => {
        el.addEventListener('input', debounce(fetchcode, 300));
    });
    
    document.getElementsByName('drawer').forEach(radio => {
        radio.addEventListener('change', fetchcode);
    });

    elements.logoScale.addEventListener('input', () => {
        elements.logoScaleValue.textContent = `${elements.logoScale.value}%`;
        fetchcode();
    });

    elements.logoInput.addEventListener('change', handleFileSelect);

    // Drag and Drop
    elements.dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.dropZone.classList.add('drag-over');
    });
    
    ['dragleave', 'dragend'].forEach(evt => {
        elements.dropZone.addEventListener(evt, () => elements.dropZone.classList.remove('drag-over'));
    });

    elements.dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.dropZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) {
            elements.logoInput.files = e.dataTransfer.files;
            handleFileSelect();
        }
    });

    function handleFileSelect() {
        if (elements.logoInput.files.length > 0) {
            elements.uploadText.textContent = elements.logoInput.files[0].name;
            fetchcode();
        }
    }

    function toggleTheme() {
        currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', currentTheme);
        localStorage.setItem('theme', currentTheme);
        updateThemeUI(currentTheme);
        fetchcode(); // Refresh QR with new theme colors if needed
    }

    function updateThemeUI(theme) {
        const iconLight = document.getElementById('theme-icon-light');
        const iconDark = document.getElementById('theme-icon-dark');
        if (theme === 'light') {
            if (iconLight) iconLight.classList.remove('d-none');
            if (iconDark) iconDark.classList.add('d-none');
            if (elements.headerLogo) elements.headerLogo.src = elements.headerLogo.getAttribute('data-light');
        } else {
            if (iconLight) iconLight.classList.add('d-none');
            if (iconDark) iconDark.classList.remove('d-none');
            if (elements.headerLogo) elements.headerLogo.src = elements.headerLogo.getAttribute('data-dark');
        }
    }

    function applyLocalization(lang) {
        const t = translations[lang];
        Object.keys(t).forEach(id => {
            const el = document.getElementById(`t-${id.replace('_', '-')}`);
            if (el) el.textContent = t[id];
        });
        if (!elements.logoInput.files.length) elements.uploadText.textContent = t.upload_text;
    }

    function updateYear() {
        const yearEl = document.getElementById('current-year');
        if (yearEl) yearEl.textContent = new Date().getFullYear();
    }

    async function fetchcode() {
        const text = elements.qrtxt.value.trim();
        if (!text) {
            elements.qrimg.classList.add('d-none');
            elements.qrimg.src = "";
            elements.qrPlaceholder.classList.remove('d-none');
            return;
        }

        const formData = new FormData();
        formData.append('text', text);
        formData.append('logo_scale', elements.logoScale.value);
        formData.append('fg_color', elements.fgColor.value);
        formData.append('bg_color', elements.bgColor.value);
        formData.append('drawer', document.querySelector('input[name="drawer"]:checked').value);
        
        if (elements.logoInput.files[0]) {
            formData.append('logo', elements.logoInput.files[0]);
        }

        try {
            const response = await fetch('/qr', { method: 'POST', body: formData });
            if (response.ok) {
                const blob = await response.blob();
                elements.qrimg.src = URL.createObjectURL(blob);
                elements.qrimg.classList.remove('d-none');
                elements.qrPlaceholder.classList.add('d-none');
            }
        } catch (error) { console.error('Error:', error); }
    }

    function debounce(func, wait) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func(...args), wait);
        };
    }
});
