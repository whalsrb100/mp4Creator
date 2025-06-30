document.addEventListener('DOMContentLoaded', function() {
    const textInput = document.getElementById('text-input');
    const charCount = document.getElementById('char-count');
    const wordCount = document.getElementById('word-count');
    const estimatedTime = document.getElementById('estimated-time');
    const voiceSelect = document.getElementById('voice-select');
    const speedInput = document.getElementById('speed-input');
    const speedValue = document.getElementById('speed-value');
    const ttsForm = document.getElementById('tts-form');
    const generateBtn = document.getElementById('generate-btn');
    const progressSection = document.getElementById('progress-section');
    const resultSection = document.getElementById('result-section');
    const audioPlayer = document.getElementById('audio-player');

    // 텍스트 통계 업데이트
    textInput.addEventListener('input', updateTextStats);
    
    // 속도 슬라이더 업데이트
    speedInput.addEventListener('input', function() {
        const value = parseInt(this.value);
        speedValue.textContent = (value >= 0 ? '+' : '') + value + '%';
    });

    // 폼 제출 처리
    ttsForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        await generateAudio();
    });

    // 텍스트 통계 업데이트 함수
    function updateTextStats() {
        const text = textInput.value;
        const chars = text.length;
        const words = text.trim() ? text.trim().split(/\s+/).length : 0;
        
        // 한국어 기준 대략적인 음성 시간 계산 (분당 150-200자 정도)
        const estimatedSeconds = Math.ceil(chars / 3); // 초당 약 3자 기준
        
        charCount.textContent = chars;
        wordCount.textContent = words;
        estimatedTime.textContent = formatTime(estimatedSeconds);
    }

    // 시간 포맷 함수
    function formatTime(seconds) {
        if (seconds < 60) {
            return seconds + '초';
        } else {
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            return minutes + '분 ' + remainingSeconds + '초';
        }
    }

    // 음성 생성 함수
    async function generateAudio() {
        const formData = new FormData(ttsForm);
        
        // 속도 값을 백분율로 변환
        const speedValue = parseInt(formData.get('speed'));
        const speedPercent = (speedValue >= 0 ? '+' : '') + speedValue + '%';
        formData.set('speed', speedPercent);
        
        // 버튼 비활성화
        generateBtn.disabled = true;
        generateBtn.textContent = '🎤 생성 중...';
        
        // 진행 상황 섹션 표시
        progressSection.style.display = 'block';
        resultSection.style.display = 'none';
        
        // 진행 상황 초기화
        updateProgress(10, '음성 생성 준비 중...');
        addLog('음성 생성을 시작합니다...', 'info');

        try {
            updateProgress(30, 'Edge-TTS로 음성 변환 중...');
            addLog(`텍스트: ${formData.get('text').substring(0, 50)}...`, 'info');
            addLog(`목소리: ${voiceSelect.options[voiceSelect.selectedIndex].text}`, 'info');
            addLog(`속도: ${speedPercent}`, 'info');

            const response = await fetch('/api/generate-audio', {
                method: 'POST',
                body: formData
            });

            updateProgress(80, '음성 파일 처리 중...');

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            updateProgress(100, '✅ 생성 완료!');
            addLog('음성 파일이 성공적으로 생성되었습니다!', 'success');

            if (result.success) {
                showResult(result, formData);
            } else {
                throw new Error(result.error || '알 수 없는 오류가 발생했습니다.');
            }

        } catch (error) {
            console.error('음성 생성 실패:', error);
            updateProgress(0, '❌ 생성 실패');
            addLog(`오류: ${error.message}`, 'error');
            
            setTimeout(() => {
                progressSection.style.display = 'none';
            }, 5000);
        }

        // 버튼 복원
        generateBtn.disabled = false;
        generateBtn.textContent = '🎤 음성 생성하기';
    }

    // 진행 상황 업데이트
    function updateProgress(percent, message) {
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        
        if (progressFill) {
            progressFill.style.width = `${percent}%`;
        }
        
        if (progressText) {
            progressText.textContent = message;
        }
    }

    // 로그 추가
    function addLog(message, type = 'info') {
        const progressLogs = document.getElementById('progress-logs');
        if (progressLogs) {
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry ${type}`;
            logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            progressLogs.appendChild(logEntry);
            progressLogs.scrollTop = progressLogs.scrollHeight;
        }
    }

    // 결과 표시
    function showResult(result, formData) {
        progressSection.style.display = 'none';
        resultSection.style.display = 'block';

        // 오디오 플레이어 설정
        if (audioPlayer && result.download_url) {
            audioPlayer.src = result.download_url;
            audioPlayer.style.display = 'block';
            audioPlayer.load();
        }

        // 결과 정보 업데이트
        document.getElementById('result-size').textContent = result.file_size || '알 수 없음';
        document.getElementById('result-duration').textContent = result.duration || '계산 중...';
        document.getElementById('result-time').textContent = new Date().toLocaleString();
        
        const selectedVoiceText = voiceSelect.options[voiceSelect.selectedIndex].text;
        document.getElementById('result-voice').textContent = selectedVoiceText;
        document.getElementById('result-speed').textContent = formData.get('speed');

        // 다운로드 버튼 설정
        const downloadBtn = document.getElementById('download-btn');
        if (downloadBtn && result.download_url) {
            downloadBtn.onclick = () => {
                const link = document.createElement('a');
                link.href = result.download_url;
                link.download = 'generated_audio.mp3';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            };
        }
    }

    // 초기화
    updateTextStats();
    updateProgress(0, '준비 완료');
});
