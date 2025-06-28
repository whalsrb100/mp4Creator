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
    // 모든 드롭다운 처리
    document.querySelectorAll('.theme-dropdown').forEach(function(dropdown) {
        const selected = dropdown.querySelector('.theme-dropdown-selected');
        const list = dropdown.querySelector('.theme-dropdown-list');
        const hiddenInput = dropdown.querySelector('input[type="hidden"]');
        
        selected.addEventListener('click', function(e) {
            e.stopPropagation();
            // 다른 드롭다운들 닫기
            document.querySelectorAll('.theme-dropdown-list').forEach(function(otherList) {
                if (otherList !== list) {
                    otherList.classList.remove('show');
                }
            });
            list.classList.toggle('show');
        });
        
        list.querySelectorAll('.theme-dropdown-item').forEach(function(item) {
            item.addEventListener('click', function() {
                list.querySelectorAll('.theme-dropdown-item').forEach(i => i.classList.remove('selected'));
                item.classList.add('selected');
                selected.textContent = item.textContent;
                if (hiddenInput) {
                    hiddenInput.value = item.dataset.value;
                }
                list.classList.remove('show');
            });
        });
    });
    
    // 문서 클릭시 모든 드롭다운 닫기
    document.addEventListener('click', function() {
        document.querySelectorAll('.theme-dropdown-list').forEach(function(list) {
            list.classList.remove('show');
        });
    });
});
