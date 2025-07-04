/**
 * Enhanced category selection fix for Sortownia application
 * This script provides robust handling of category selection in the sorted bag forms
 */

document.addEventListener('DOMContentLoaded', function() {
    // Find all category selection cards
    const categoryCards = document.querySelectorAll('.category-card');
    if (!categoryCards.length) {
        console.log('No category cards found');
        return;
    }

    console.log(`Found ${categoryCards.length} category cards`);

    // Function to handle category selection
    function selectCategory(card) {
        // Get the radio input inside the card
        const radio = card.querySelector('input[type="radio"]');
        if (!radio) {
            console.error('No radio button found in card:', card);
            return;
        }

        console.log('Selecting category:', radio.value);

        // First ensure we explicitly check the radio
        radio.checked = true;

        // Remove selection class from all cards
        categoryCards.forEach(c => c.classList.remove('selected'));
        
        // Add selection class to this card
        card.classList.add('selected');
        
        // Dispatch proper change events
        radio.dispatchEvent(new Event('change', { bubbles: true }));
        
        // If this is part of a wizard, enable the next button
        const nextButton = document.getElementById('step1Next');
        if (nextButton) {
            nextButton.disabled = false;
        }
        
        // Add visual feedback animation
        card.style.transform = 'scale(1.05)';
        setTimeout(() => {
            card.style.transform = '';
        }, 200);
        
        console.log('Category selected:', radio.value);
    }

    // Set up each card with the appropriate event handlers
    categoryCards.forEach((card, index) => {
        const radio = card.querySelector('input[type="radio"]');
        if (!radio) {
            console.error('Card has no radio button:', index);
            return;
        }
        
        // Set initial selected state if the radio is already checked
        if (radio.checked) {
            card.classList.add('selected');
            console.log('Initially selected category:', radio.value);
            
            // Enable next button if in wizard
            const nextButton = document.getElementById('step1Next');
            if (nextButton) {
                nextButton.disabled = false;
            }
        }
        
        // Attach click handler
        card.addEventListener('click', function(e) {
            // Prevent any default behavior
            e.preventDefault();
            e.stopPropagation();
            
            // Select this category
            selectCategory(card);
        });
        
        // Ensure radio changes also update UI
        radio.addEventListener('change', function() {
            if (this.checked) {
                selectCategory(card);
            }
        });
    });
    
    // Ensure any pre-selected categories are properly styled
    // This is a fallback to catch any initial state issues
    setTimeout(() => {
        categoryCards.forEach(card => {
            const radio = card.querySelector('input[type="radio"]');
            if (radio && radio.checked) {
                card.classList.add('selected');
                console.log('Catching pre-selected category:', radio.value);
            }
        });
    }, 100);
});