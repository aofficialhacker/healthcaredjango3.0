console.log("Script loaded successfully");

document.addEventListener("DOMContentLoaded", function() {
  console.log("DOM fully loaded, initializing functionalities.");

  // Form validation (if needed)
  const forms = document.querySelectorAll('.needs-validation');
  forms.forEach(function(form) {
    form.addEventListener('submit', function(event) {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add('was-validated');
    }, false);
  });

  // Toggle password visibility functionality (if applicable)
  const togglePasswordButtons = document.querySelectorAll('.toggle-password');
  console.log("Found", togglePasswordButtons.length, "toggle password buttons.");
  togglePasswordButtons.forEach(function(button) {
    button.addEventListener('click', function() {
      console.log("Toggle button clicked.");
      // Find the closest container with class "position-relative"
      const container = button.closest('.position-relative');
      console.log("Container:", container);
      if (!container) return;
      // Find the input within that container
      const input = container.querySelector('input');
      console.log("Password input found:", input);
      if (!input) return;
      if (input.getAttribute('type') === "password") {
        input.setAttribute('type', 'text');
        button.classList.add('reverse'); // We'll control the icon via CSS
      } else {
        input.setAttribute('type', 'password');
        button.classList.remove('reverse');
      }
    });
  });

  // Real-time search for doctor list (if search box exists)
  const doctorSearchInput = document.getElementById('doctorSearch');
  if (doctorSearchInput) {
    doctorSearchInput.addEventListener('keyup', function() {
      const searchTerm = this.value.toLowerCase();
      const doctorCards = document.querySelectorAll('.doctor-card');
      doctorCards.forEach(function(card) {
        // Get the doctor's name and specialty text
        const nameElem = card.querySelector('.doctor-name');
        const specialtyElem = card.querySelector('.doctor-specialty');
        const nameText = nameElem ? nameElem.textContent.toLowerCase() : '';
        const specialtyText = specialtyElem ? specialtyElem.textContent.toLowerCase() : '';
        // Show the card if the search term is found in either field; otherwise hide it.
        if (nameText.includes(searchTerm) || specialtyText.includes(searchTerm)) {
          card.style.display = "block";
        } else {
          card.style.display = "none";
        }
      });
    });
  }
});
