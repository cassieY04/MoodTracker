//ik we shldnt use javascript but this is the best/easiest way aka more user friendly to do, i only use it purely for light/dark mode(from jiaqi)
(function() {
})();

document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const html = document.documentElement;

    //Sync icon on load based on what Flask set
    const currentTheme = html.getAttribute('data-theme');
    if (themeIcon && currentTheme === 'dark') {
        themeIcon.classList.replace('fa-moon', 'fa-sun');
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const isDark = html.getAttribute('data-theme') === 'dark';
            const newTheme = isDark ? 'light' : 'dark';
            
            html.setAttribute('data-theme', newTheme);
            
            //Update Icon
            if (themeIcon) {
                if (newTheme === 'dark') {
                    themeIcon.classList.replace('fa-moon', 'fa-sun');
                } else {
                    themeIcon.classList.replace('fa-sun', 'fa-moon');
                }
            }

            //makes it unique to the user
            fetch('/update_theme', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ theme: newTheme })
            });
        });
    }
});