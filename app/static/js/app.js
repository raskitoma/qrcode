const translations = {
    en: {
        title: "Generate QR",
        subtitle: "Create custom QR codes with your brand logo in seconds.",
        label_text: "QR Content",
        label_logo: "Logo (optional)",
        upload_text: "Choose image...",
        label_size: "Logo Size",
        placeholder: "Waiting for content...",
        rights: "All Rights Reserved."
    },
    es: {
        title: "Generar QR",
        subtitle: "Crea códigos QR personalizados con tu logo en segundos.",
        label_text: "Contenido del QR",
        label_logo: "Logo (opcional)",
        upload_text: "Elegir imagen...",
        label_size: "Tamaño del Logo",
        placeholder: "Esperando contenido...",
        rights: "Todos los derechos reservados."
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const qrimg = document.getElementById('qrcodeimg');
    const qrtxt = document.getElementById('qrtext');
    const logoInput = document.getElementById('logo');
    const logoScale = document.getElementById('logo_scale');
    const logoScaleValue = document.getElementById('logo-scale-value');
    const qrPlaceholder = document.getElementById('qr-placeholder');
    const themeToggle = document.getElementById('theme-toggle');
    const headerLogo = document.getElementById('header-logo');
    const langSelect = document.getElementById('lang-select');
    const uploadText = document.getElementById('t-upload-text');

    // State
    let currentTheme = localStorage.getItem('theme') || 'dark';
    let currentLang = localStorage.getItem('lang') || 'en';

    // Initialize UI
    document.documentElement.setAttribute('data-theme', currentTheme);
    langSelect.value = currentLang;
    updateYear();
    applyLocalization(currentLang);
    updateThemeUI(currentTheme);

    // Events
    themeToggle.addEventListener('click', toggleTheme);
    langSelect.addEventListener('change', (e) => {
        currentLang = e.target.value;
        localStorage.setItem('lang', currentLang);
        applyLocalization(currentLang);
    });

    qrtxt.addEventListener('input', debounce(fetchcode, 300));
    logoInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadText.textContent = e.target.files[0].name;
        } else {
            uploadText.textContent = translations[currentLang].upload_text;
        }
        fetchcode();
    });
    logoScale.addEventListener('input', () => {
        logoScaleValue.textContent = `${logoScale.value}%`;
        fetchcode();
    });

    // Functions
    function toggleTheme() {
        currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', currentTheme);
        localStorage.setItem('theme', currentTheme);
        updateThemeUI(currentTheme);
    }

    function updateThemeUI(theme) {
        const iconLight = document.getElementById('theme-icon-light');
        const iconDark = document.getElementById('theme-icon-dark');
        
        if (theme === 'light') {
            iconLight.classList.remove('d-none');
            iconDark.classList.add('d-none');
            headerLogo.src = '/img/rask_logo-black.svg';
        } else {
            iconLight.classList.add('d-none');
            iconDark.classList.remove('d-none');
            headerLogo.src = '/img/rask_logo-white.svg';
        }
    }

    function applyLocalization(lang) {
        const t = translations[lang];
        document.getElementById('t-title').textContent = t.title;
        document.getElementById('t-subtitle').textContent = t.subtitle;
        document.getElementById('t-label-text').textContent = t.label_text;
        document.getElementById('t-label-logo').textContent = t.label_logo;
        document.getElementById('t-label-size').textContent = t.label_size;
        document.getElementById('t-placeholder').textContent = t.placeholder;
        document.getElementById('t-rights').textContent = t.rights;
        
        // Update upload text if no file selected
        if (!logoInput.files.length) {
            uploadText.textContent = t.upload_text;
        }
    }

    function updateYear() {
        document.getElementById('current-year').textContent = new Date().getFullYear();
    }

    async function fetchcode() {
        const text = qrtxt.value.trim();
        if (!text) {
            qrimg.classList.add('d-none');
            qrPlaceholder.classList.remove('d-none');
            return;
        }

        const formData = new FormData();
        formData.append('text', text);
        formData.append('logo_scale', logoScale.value);
        if (logoInput.files[0]) {
            formData.append('logo', logoInput.files[0]);
        }

        try {
            const response = await fetch('/qr', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const blob = await response.blob();
                const imageUrl = URL.createObjectURL(blob);
                qrimg.src = imageUrl;
                qrimg.classList.remove('d-none');
                qrPlaceholder.classList.add('d-none');
            }
        } catch (error) {
            console.error('Error fetching QR code:', error);
        }
    }

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
});
