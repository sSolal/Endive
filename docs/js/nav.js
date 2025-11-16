// Navigation component for Endive website

document.addEventListener('DOMContentLoaded', function() {
    // Get current page
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';

    // Find and mark active navigation link
    const navLinks = document.querySelectorAll('.nav-links a');
    navLinks.forEach(link => {
        const linkPage = link.getAttribute('href');
        if (linkPage === currentPage ||
            (currentPage === '' && linkPage === 'index.html') ||
            (currentPage === 'index.html' && linkPage === 'index.html')) {
            link.classList.add('active');
        }
    });
});
