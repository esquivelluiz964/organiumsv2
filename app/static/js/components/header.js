document.addEventListener('DOMContentLoaded', function() {
  // Elementos do DOM
  const mobileNavToggle = document.querySelector('.mobile-nav-toggle');
  const mobileNav = document.querySelector('.mobile-nav');
  const closeMobileNav = document.querySelector('.close-mobile-nav');
  const userAvatar = document.querySelector('.user-avatar');
  const userDropdown = document.querySelector('.user-dropdown');
  
  // Alternar menu mobile
  if (mobileNavToggle && mobileNav) {
    mobileNavToggle.addEventListener('click', function() {
      mobileNav.classList.add('active');
      document.body.style.overflow = 'hidden'; // Previne scroll quando menu está aberto
    });
  }
  
  // Fechar menu mobile
  if (closeMobileNav && mobileNav) {
    closeMobileNav.addEventListener('click', function() {
      mobileNav.classList.remove('active');
      document.body.style.overflow = ''; // Restaura scroll
    });
  }
  
  // Fechar menu mobile ao clicar em um link
  const mobileNavLinks = document.querySelectorAll('.mobile-nav .nav-link');
  mobileNavLinks.forEach(link => {
    link.addEventListener('click', function() {
      mobileNav.classList.remove('active');
      document.body.style.overflow = '';
    });
  });
  
  // Alternar dropdown do usuário
  if (userAvatar && userDropdown) {
    userAvatar.addEventListener('click', function(e) {
      e.stopPropagation();
      userDropdown.classList.toggle('active');
    });
  }
  
  // Fechar dropdown ao clicar fora dele
  document.addEventListener('click', function(e) {
    if (userDropdown && userDropdown.classList.contains('active') && 
        !userDropdown.contains(e.target) && 
        e.target !== userAvatar) {
      userDropdown.classList.remove('active');
    }
  });
  
  // Fechar menu mobile ao redimensionar a janela para desktop
  window.addEventListener('resize', function() {
    if (window.innerWidth > 768 && mobileNav.classList.contains('active')) {
      mobileNav.classList.remove('active');
      document.body.style.overflow = '';
    }
  });
});