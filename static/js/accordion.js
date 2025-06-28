document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.accordion-header').forEach(function(header) {
        header.addEventListener('click', function() {
            const content = header.nextElementSibling;
            if (content.style.display === 'block') {
                content.style.display = 'none';
            } else {
                content.style.display = 'block';
            }
            header.classList.toggle('active');
        });
    });
    // 테마 드롭다운
    const dropdown = document.querySelector('.theme-dropdown');
    if (dropdown) {
        const selected = dropdown.querySelector('.theme-dropdown-selected');
        const list = dropdown.querySelector('.theme-dropdown-list');
        selected.addEventListener('click', function(e) {
            e.stopPropagation();
            list.classList.toggle('show');
        });
        list.querySelectorAll('.theme-dropdown-item').forEach(function(item) {
            item.addEventListener('click', function() {
                list.querySelectorAll('.theme-dropdown-item').forEach(i => i.classList.remove('selected'));
                item.classList.add('selected');
                selected.textContent = item.textContent;
                document.querySelector('input[name="theme"]').value = item.dataset.value;
                list.classList.remove('show');
            });
        });
        document.addEventListener('click', function() {
            list.classList.remove('show');
        });
    }
});
