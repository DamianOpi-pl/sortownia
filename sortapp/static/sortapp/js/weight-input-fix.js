/**
 * Weight Input Fix - Handles numeric input issues on mobile devices
 * 
 * This script fixes the issue where typing a second digit in number inputs
 * replaces the first digit instead of appending to it, which is common
 * on some mobile browsers.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Find all weight input fields
    const weightInputs = document.querySelectorAll('input[name="weight"]');
    
    weightInputs.forEach(function(input) {
        // Convert any NumberInput to text with numeric characteristics
        if (input.type === 'number') {
            input.type = 'text';
            input.inputMode = 'numeric';
            input.pattern = '[0-9]*';
        }
        
        // Add event listeners for input validation
        input.addEventListener('input', function(e) {
            // Keep only digits
            let value = this.value.replace(/[^0-9]/g, '');
            
            // Update input value only if it changed to avoid cursor jumping
            if (this.value !== value) {
                this.value = value;
            }
        });
        
        // Validate on blur to ensure it's a valid number
        input.addEventListener('blur', function() {
            let value = parseInt(this.value, 10);
            
            // If empty or not a number, clear it
            if (isNaN(value) || value <= 0) {
                this.value = '';
                this.classList.remove('is-valid');
                if (this.value !== '') {
                    this.classList.add('is-invalid');
                }
            } else {
                // Format as a whole number
                this.value = value.toString();
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            }
        });
        
        // Ensure numeric keyboard on mobile
        input.addEventListener('focus', function() {
            // Some browsers need this attribute to be set on focus
            this.inputMode = 'numeric';
        });
    });
});