<template>
  <div class="songs-view">
    <div class="songs-layout">
      <aside class="song-list">
        <div class="list-header">
          <div>
            <h2>歌曲练习</h2>
            <p>选歌后直接开练</p>
          </div>
          <button class="ghost-btn" @click="scanSongs">扫描目录</button>
        </div>

        <label class="search-box">
          <span>快速定位</span>
          <input v-model.trim="searchQuery" type="text" placeholder="搜索歌曲名或版本关键词" />
        </label>

        <div v-if="recentPracticeLinks.length" class="recent-practice-block">
          <div class="section-heading">
            <h4>最近练习</h4>
            <span class="section-copy">最近 3 条</span>
          </div>
          <div class="recent-practice-list">
            <button
              v-for="item in recentPracticeLinks"
              :key="item.id"
              class="recent-practice-card"
              @click="openRecentPractice(item)"
            >
              <div class="recent-practice-card-head">
                <strong>{{ item.songTitle }}</strong>
                <span class="recent-practice-jump">继续</span>
              </div>
              <p>{{ item.version }}</p>
              <div class="media-hints recent-practice-meta">
                <span>{{ item.audioLabel }}</span>
                <span>{{ item.playbackRate.toFixed(2) }}x</span>
                <span v-if="item.loopLabel">{{ item.loopLabel }}</span>
              </div>
            </button>
          </div>
        </div>

        <div v-if="loading" class="state-box">加载歌曲中...</div>
        <div v-else-if="songs.length === 0" class="state-box">
          暂无歌曲，可先将文件放到 `library/songs/`
        </div>
        <div v-else-if="filteredSongs.length === 0" class="state-box">
          没找到匹配的歌曲，换个关键词试试
        </div>
        <button
          v-for="song in filteredSongs"
          v-else
          :key="song.id"
          :class="['song-card', { active: selectedSong?.id === song.id }]"
          @click="selectSong(song)"
        >
          <strong>{{ song.title }}</strong>
          <p>{{ song.artist || '未填写歌手' }}</p>
          <span>{{ song.versions.length }} 个版本</span>
        </button>
      </aside>

      <section class="song-detail">
        <div v-if="!selectedSong" class="state-box">
          选择左侧歌曲开始练习
        </div>
        <template v-else>
          <div class="detail-header">
            <div>
              <h3>{{ selectedSong.title }}</h3>
              <p>{{ selectedSong.artist || '未填写歌手' }}</p>
            </div>
            <div class="detail-header-actions">
              <span class="path-pill">{{ selectedSong.path }}</span>
              <button class="danger-btn" :disabled="loading" @click="deleteSelectedSong">
                {{ loading ? '处理中...' : '删除歌曲' }}
              </button>
            </div>
          </div>

          <div class="versions-section">
            <div class="section-heading">
              <h4>版本导航</h4>
              <span class="section-copy">{{ versionGroups.length }} 个主版本</span>
            </div>

            <div
              v-if="showVersionGroups"
              class="group-grid"
              :style="gridColumnsStyle(versionGroups.length, 5)"
            >
              <button
                v-for="group in versionGroups"
                :key="group.name"
                :class="['group-item', { active: currentGroupName === group.name }]"
                @click="selectVersionGroup(group)"
              >
                <strong>{{ group.name }}</strong>
                <small>{{ groupSummary(group) }}</small>
              </button>
            </div>

            <div v-if="currentVersionGroup?.segments?.length" class="segments-section">
              <div class="section-heading">
                <h4>练习段落</h4>
                <span class="section-copy">
                  {{ currentVersionGroup.segments.length }} 个段落
                </span>
              </div>

              <div class="versions-grid" :style="gridColumnsStyle(currentVersionOptionCount, 5)">
                <button
                  v-if="currentVersionGroup.root"
                  :class="['version-item', { active: selectedVersion === currentVersionGroup.root.name }]"
                  @click="selectVersion(currentVersionGroup.root)"
                >
                  <span>整版资料</span>
                  <small>{{ versionSummary(currentVersionGroup.root) }}</small>
                </button>
                <button
                  v-for="version in currentVersionGroup.segments"
                  :key="version.name"
                  :class="['version-item', { active: selectedVersion === version.name }]"
                  @click="selectVersion(version)"
                >
                  <span>{{ versionLeafLabel(version.name) }}</span>
                  <small>{{ versionSummary(version) }}</small>
                </button>
              </div>
            </div>

            <div
              v-else-if="showStandaloneVersions"
              class="versions-grid"
              :style="gridColumnsStyle(selectedSong.versions.length, 5)"
            >
              <button
                v-for="version in selectedSong.versions"
                :key="version.name"
                :class="['version-item', { active: selectedVersion === version.name }]"
                @click="selectVersion(version)"
              >
                <span>{{ version.name }}</span>
                <small>{{ versionSummary(version) }}</small>
              </button>
            </div>
          </div>

          <div class="player-section" v-if="selectedVersion">
            <div class="practice-shell">
              <div class="practice-main">
                <div class="player-header">
                  <div class="player-header-copy">
                    <span class="player-header-eyebrow">当前版本</span>
                    <strong>{{ selectedVersion }}</strong>
                  </div>
                  <div class="player-header-actions">
	                    <div class="playback-mode-group">
                      <label class="playback-mode-option">
                        <input v-model="playbackMode" type="radio" value="normal">
                        <span>正常播放</span>
                      </label>
                      <label class="playback-mode-option">
                        <input v-model="playbackMode" type="radio" value="mix">
                        <span>内录混音</span>
                      </label>
                      <label class="playback-mode-option">
                        <input v-model="playbackMode" type="radio" value="video">
                        <span>音画同录</span>
	                      </label>
	                    </div>
	                    <button
	                      :class="['play-btn', playbackButtonTone]"
	                      :disabled="!currentAudioFile || coachAnalyzing || hasPendingCoachTake"
	                      @click="handlePlaybackAction"
	                    >
	                      <span class="play-btn-icon" aria-hidden="true">{{ playbackButtonIcon }}</span>
	                      <span>{{ playbackButtonLabel }}</span>
	                    </button>
                  </div>
                </div>
                <div class="player-mode-hint">
                  <span class="coach-badge">{{ currentPlaybackModeLabel }}</span>
                  <span>{{ playbackModeDescription }}</span>
                </div>

                <div class="transport-bar">
                  <input
                    class="seek-slider"
                    type="range"
                    min="0"
                    :max="duration || 0"
                    step="0.1"
                    :value="currentTime"
                    :disabled="!duration"
                    @input="seekAudioRange"
                  />
                  <div class="transport-meta">
                    <div class="time-row">
                      <span>{{ formatTime(currentTime) }}</span>
                      <span>{{ formatTime(duration) }}</span>
                    </div>

                    <div class="control-row loop-row">
                      <button :class="{ active: loopStart !== null }" @click="setLoopStart">
                        A {{ loopStart === null ? '--:--' : formatTime(loopStart) }}
                      </button>
                      <button :class="{ active: loopEnd !== null }" @click="setLoopEnd">
                        B {{ loopEnd === null ? '--:--' : formatTime(loopEnd) }}
                      </button>
                      <button @click="clearLoop">清除循环</button>
                    </div>
                  </div>

                  <div class="control-row speed-row">
                    <span>速度</span>
                    <button
                      v-for="speed in speeds"
                      :key="speed"
                      :class="{ active: playbackRate === speed }"
                      @click="setSpeed(speed)"
                    >
                      {{ speed }}x
                    </button>
                  </div>

                  <div class="control-row volume-row">
                    <span>伴奏音量</span>
                    <input
                      class="volume-slider"
                      type="range"
                      min="0"
                      max="150"
                      step="1"
                      :value="backingVolumePercent"
                      @input="setBackingVolume"
                    />
                    <strong>{{ backingVolumePercent }}%</strong>
                  </div>

                  <div class="loop-snippet-panel">
                    <div class="loop-snippet-head">
                      <div>
                        <strong>打点片段</strong>
                        <p>按当前伴奏保存常练小段，后面直接一键套用。</p>
                        <p class="loop-snippet-current">当前伴奏：{{ currentAudioLabel }}</p>
                      </div>
                      <span class="coach-badge">{{ currentLoopSnippets.length }} 条</span>
                    </div>
                    <div class="loop-snippet-form">
                      <input
                        v-model.trim="loopSnippetDraft"
                        type="text"
                        placeholder="片段简介，例如：尾奏第2句 / 主歌切分"
                      >
                      <button
                        class="ghost-btn"
                        :disabled="loopStart === null || loopEnd === null || !loopSnippetDraft"
                        @click="saveCurrentLoopSnippet"
                      >
                        保存片段
                      </button>
                    </div>
                    <div v-if="currentLoopSnippets.length" class="loop-snippet-list">
                      <article
                        v-for="snippet in currentLoopSnippets"
                        :key="snippet.id"
                        class="loop-snippet-card"
                      >
                        <div class="loop-snippet-meta">
                          <button class="loop-snippet-link" @click="applyLoopSnippet(snippet)">{{ snippet.label }}</button>
                          <p>{{ formatTime(snippet.start) }} - {{ formatTime(snippet.end) }}</p>
                        </div>
                        <div class="loop-snippet-actions">
                          <button class="ghost-btn danger-ghost" @click="deleteLoopSnippet(snippet.id)">删除</button>
                        </div>
                      </article>
                    </div>
                    <div v-else class="empty-copy compact-empty">当前这条伴奏下还没有保存片段。先设 A/B，再写一句简介保存。</div>
                    <div v-if="siblingLoopSnippetGroups.length" class="loop-snippet-sibling-groups">
                      <span class="audio-options-label">这个版本其他伴奏下已保存</span>
                      <div class="loop-snippet-sibling-list">
                        <button
                          v-for="group in siblingLoopSnippetGroups"
                          :key="group.path"
                          class="audio-option-btn"
                          @click="selectAudioOption(group.path)"
                        >
                          {{ group.label }} · {{ group.snippets.length }} 条
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="support-grid">
                <div class="score-section">
                  <div class="score-header">
                    <h4>谱面与标记</h4>
                    <button class="ghost-btn" :disabled="!currentAudioFile" @click="addMarker">
                      添加标记
                    </button>
                  </div>

                  <div class="score-actions">
                    <button v-if="selectedVersionFiles.pdf" @click="openScore('pdf')">打开 PDF</button>
                    <button v-if="selectedVersionFiles.gp" @click="openScore('gp')">打开 GP</button>
                    <a
                      v-if="referenceFiles.video"
                      :href="buildSongMediaUrl(referenceFiles.video)"
                      target="_blank"
                      rel="noreferrer"
                    >
                      打开参考视频
                    </a>
                    <a
                      v-if="referenceFiles.image"
                      :href="buildSongMediaUrl(referenceFiles.image)"
                      target="_blank"
                      rel="noreferrer"
                    >
                      打开参考图片
                    </a>
                  </div>

                  <div class="media-hints">
                    <span v-if="currentAudioFile">当前版本有音频</span>
                    <span v-else>当前版本没有独立伴奏</span>
                    <span v-if="referenceFiles.video">同组带参考视频</span>
                    <span v-if="referenceFiles.image">同组带参考图</span>
                  </div>

                  <div v-if="audioOptions.length > 1" class="audio-options">
                    <span class="audio-options-label">当前音频</span>
                    <div class="audio-options-list">
                      <button
                        v-for="option in audioOptions"
                        :key="option.path"
                        :class="['audio-option-btn', { active: selectedAudioFile === option.path }]"
                        @click="selectAudioOption(option.path)"
                      >
                        {{ option.label }}
                      </button>
                    </div>
                  </div>

                  <div class="markers-list" v-if="visibleMarkers.length">
                    <button
                      v-for="(marker, index) in visibleMarkers"
                      :key="`${marker.version}-${index}`"
                      class="marker-item"
                      @click="seekToTime(marker.time)"
                    >
                      <strong>{{ formatTime(marker.time) }}</strong>
                      <span>{{ marker.label }}</span>
                    </button>
                  </div>
                  <div v-else class="empty-copy">当前版本暂无标记</div>
                </div>

                <div class="score-section">
                  <div class="score-header">
                    <div>
                      <h4>相关学习视频</h4>
                      <p class="coach-copy">自动关联这首歌的弹唱、教学和 solo 参考。</p>
                    </div>
                    <span class="coach-badge">{{ relatedVideos.length }} 个视频</span>
                  </div>

                  <div v-if="relatedVideosLoading" class="empty-copy">正在匹配相关学习视频...</div>
                  <div v-else-if="relatedVideos.length" class="related-video-list">
                    <article
                      v-for="video in relatedVideos"
                      :key="video.id"
                      class="related-video-card"
                    >
                      <div class="related-video-thumb">
                        <img
                          v-if="video.thumbnail"
                          :src="buildRelatedVideoThumbnailUrl(video)"
                          alt=""
                        >
                        <span v-else>相关视频</span>
                      </div>
                      <div class="related-video-main">
                        <strong>{{ video.title }}</strong>
                        <p>{{ video.author || video.category || '本地学习视频' }}</p>
                        <div class="media-hints">
                          <span v-for="reason in video.match_reasons" :key="`${video.id}-${reason}`">{{ reason }}</span>
                        </div>
                      </div>
                      <div class="related-video-actions">
                        <button class="ghost-btn" @click="openRelatedVideo(video)">打开视频</button>
                      </div>
                    </article>
                  </div>
                  <div v-else class="empty-copy">当前还没有自动匹配到相关学习视频。</div>
                </div>
                </div>
              </div>

              <aside class="practice-side">
                <div class="practice-side-tabs">
                  <button
                    :class="['practice-tab-btn', { active: practiceSideTab === 'record' }]"
                    @click="setPracticeSideTab('record')"
                  >
                    录制回放
                  </button>
                  <button
                    :class="['practice-tab-btn', { active: practiceSideTab === 'history' }]"
                    @click="setPracticeSideTab('history')"
                  >
                    练习记录
                  </button>
                </div>

                <div v-if="practiceSideTab === 'record'" class="coach-section">
                  <div class="score-header">
                    <div>
                      <h4>录制回放</h4>
                      <p class="coach-copy">这里用于录音、录像、试听和保存练习回放。</p>
                    </div>
                    <span class="coach-badge">推荐输入：Scarlett 2i2</span>
                  </div>

                  <div class="coach-actions">
                    <button
                      class="ghost-btn"
                      :disabled="isRecording || coachAnalyzing || (!coachResult && !hasPendingCoachTake)"
                      @click="resetCoachResult"
                    >
                      清空本次
                    </button>
                  </div>

                  <div class="media-hints">
                    <span>{{ coachStatusText }}</span>
                    <span v-if="coachRecordingDuration">录音时长 {{ coachRecordingDuration.toFixed(1) }}s</span>
                    <span v-if="coachCountdown > 0">音画同录倒计时 {{ coachCountdown }} 秒</span>
                    <span v-if="!recordingSupported">当前浏览器不支持录音</span>
                  </div>

                  <div v-if="learningRecommendationsLoading || learningRecommendations" class="coach-block coach-block-compact">
                    <h5>下一步建议</h5>
                    <p v-if="learningRecommendationsLoading">正在整理当前这首歌更适合先补什么。</p>
                    <template v-else-if="learningRecommendations">
                      <p><strong>{{ learningRecommendations.next_task?.title || learningRecommendations.focus_topic }}</strong></p>
                      <p>{{ learningRecommendations.next_task?.action || learningRecommendations.reason }}</p>
                      <div class="media-hints compact-hints">
                        <span v-if="learningRecommendations.focus_tag">{{ learningRecommendations.focus_tag }}</span>
                        <span v-if="learningRecommendations.next_task?.minutes">先练 {{ learningRecommendations.next_task.minutes }} 分钟</span>
                        <span v-if="learningRecommendations.next_task?.verify_step">{{ learningRecommendations.next_task.verify_step }}</span>
                      </div>
                    </template>
                  </div>

                  <div v-if="coachError" class="coach-error">{{ coachError }}</div>

                  <div v-if="pendingCoachTake" class="coach-result pending-coach-result">
                    <div class="coach-block pending-coach-head">
                      <h5>本次录制已完成</h5>
                      <p>先听一遍回放。如果满意就保存进入练习记录；如果不满意，直接重录这一段。</p>
                      <div class="media-hints compact-hints">
                        <span>{{ pendingCoachTake.captureMode === 'video' ? '音画同录' : '内录混音' }}</span>
                        <span>{{ pendingCoachTake.recordingDuration.toFixed(1) }}s</span>
                        <span>{{ playbackRate }}x</span>
                      </div>
                    </div>

                    <div class="coach-block">
                      <h5>录制预览</h5>
                      <video
                        v-if="pendingCoachTake.captureMode === 'video'"
                        class="coach-video-player"
                        controls
                        playsinline
                        :src="coachRecordingUrl"
                      ></video>
                      <audio v-else controls :src="coachRecordingUrl"></audio>
                    </div>

                    <div class="coach-actions pending-actions">
                      <button class="ghost-btn cancel-btn" :disabled="coachAnalyzing" @click="cancelPendingCoachTake">
                        Cancel
                      </button>
                      <button class="ghost-btn retry-btn" :disabled="coachAnalyzing" @click="retryPendingCoachTake">
                        Retry
                      </button>
                      <button class="play-btn save-btn" :disabled="coachAnalyzing" @click="savePendingCoachTake">
                        Save
                      </button>
                    </div>
                  </div>

                  <div v-else-if="coachResult && (coachResult.mix_url || coachResult.recording_url)" class="coach-result">
                    <div class="coach-block">
                      <h5>练习回放</h5>
                      <video
                        v-if="isVideoReplay(coachResult)"
                        class="coach-video-player"
                        controls
                        playsinline
                        :src="coachResult.mix_url || coachResult.recording_url"
                      ></video>
                      <audio v-else controls :src="coachResult.mix_url || coachResult.recording_url"></audio>
                      <a class="ghost-link" :href="coachResult.mix_url || coachResult.recording_url" download>
                        下载回放
                      </a>
                    </div>
                  </div>
                  <div v-else class="empty-copy compact-empty">开始一次内录混音或音画同录后，这里会出现录制预览和练习回放。</div>
                </div>

                <div v-if="practiceSideTab === 'history'" class="coach-section">
                  <div class="score-header">
                    <div>
                      <h4>练习记录</h4>
                      <p class="coach-copy">回放、删除和导出都在这里。</p>
                      <p v-if="lastSavedCoachSessionId" class="coach-copy coach-copy-success">刚刚保存了一条新的练习记录。</p>
                    </div>
                    <span class="coach-badge">{{ visibleCoachHistory.length }} 条记录</span>
                  </div>

                  <div class="coach-actions">
                    <button
                      class="ghost-btn"
                      :disabled="coachAnalyzing || !hasSelectedCoachSessions"
                      @click="deleteSelectedCoachSessions"
                    >
                      删除选中
                    </button>
                    <button
                      class="ghost-btn"
                      :disabled="coachAnalyzing || !hasSelectedCoachSessions"
                      @click="exportSelectedCoachSessions"
                    >
                      导出选中
                    </button>
                  </div>

                  <div v-if="visibleCoachHistory.length" class="coach-history-list">
                    <article
                      v-for="session in visibleCoachHistory"
                      :key="session.session_id"
                      :class="['coach-history-card', { fresh: session.session_id === lastSavedCoachSessionId }]"
                    >
                      <span class="coach-history-rail"></span>
                      <label class="coach-history-select">
                        <input
                          type="checkbox"
                          :checked="selectedVisibleCoachSessionIds.includes(session.session_id)"
                          @change="toggleCoachSessionSelection(session.session_id)"
                        >
                        <span>选择</span>
                      </label>

                      <div class="coach-history-head">
                        <div>
                          <strong>{{ session.song_title }} / {{ session.segment || session.version }}</strong>
                          <p>{{ formatCoachTimestamp(session.created_at) }} · {{ session.tempo_mode }}</p>
                        </div>
                        <span class="coach-history-score">{{ isVideoReplay(session) ? '视频回放' : '音频回放' }}</span>
                      </div>

                      <div class="coach-history-media">
                        <div class="coach-media-player">
                          <span>练习回放（录音 + 伴奏）</span>
                          <video
                            v-if="isVideoReplay(session)"
                            class="coach-video-player"
                            controls
                            playsinline
                            :src="session.mix_url || session.recording_url"
                          ></video>
                          <audio v-else controls :src="session.mix_url || session.recording_url"></audio>
                          <a class="ghost-link" :href="session.mix_url || session.recording_url" download>
                            下载回放
                          </a>
                        </div>
                      </div>

                    </article>
                  </div>
                  <div v-else class="empty-copy compact-empty">还没有练习记录。录完一遍后会自动出现在这里。</div>
                </div>
              </aside>
            </div>
          </div>
        </template>
      </section>
    </div>

    <div v-if="showScoreModal" class="score-modal" @click.self="closeScoreModal">
      <div class="score-modal-content">
        <div class="score-modal-header">
          <span>{{ selectedSong?.title }} / {{ selectedVersion }}</span>
          <div class="score-modal-actions">
            <a v-if="scoreUrl" class="ghost-link" :href="scoreUrl" target="_blank" rel="noreferrer">
              打开原文件
            </a>
            <button class="ghost-btn" @click="closeScoreModal">关闭</button>
          </div>
        </div>

        <div class="score-viewer">
          <div v-if="scoreNotice" class="score-notice">{{ scoreNotice }}</div>
          <div v-if="scoreType === 'gp'" class="gp-shell">
            <div v-if="gpLoading" class="empty-copy">正在加载 GP 谱...</div>
            <div v-else-if="gpError" class="empty-copy">
              {{ gpError }}
              <a class="inline-score-link" :href="scoreUrl" target="_blank" rel="noreferrer">打开原始 GP 文件</a>
            </div>
            <div v-else ref="gpContainer" class="gp-container"></div>
          </div>
          <div v-else class="pdf-container">
            <iframe :src="scoreUrl" title="PDF 曲谱预览"></iframe>
          </div>
        </div>

        <div class="modal-audio-controls">
          <div class="modal-toolbar">
            <div class="modal-primary-controls">
              <button class="modal-play-btn" :disabled="!currentAudioFile" @click="togglePlay">
                {{ isPlaying ? '暂停' : '播放' }}
              </button>
              <div class="modal-status-chip">
                <span>进度</span>
                <strong>{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</strong>
              </div>
            </div>

            <div class="modal-utility-controls">
              <div class="modal-loop-cluster">
                <div class="modal-status-chip">
                  <span>A 点</span>
                  <strong>{{ loopStart === null ? '--:--' : formatTime(loopStart) }}</strong>
                </div>
                <button @click="setLoopStart">设 A</button>
                <div class="modal-status-chip">
                  <span>B 点</span>
                  <strong>{{ loopEnd === null ? '--:--' : formatTime(loopEnd) }}</strong>
                </div>
                <button @click="setLoopEnd">设 B</button>
                <button @click="clearLoop">清除</button>
              </div>

              <div class="modal-speed-cluster">
                <span class="speed-label">速度</span>
                <div class="speed-options">
                  <button
                    v-for="speed in speeds"
                    :key="`modal-${speed}`"
                    :class="{ active: playbackRate === speed }"
                    @click="setSpeed(speed)"
                  >
                    {{ speed }}x
                  </button>
                </div>
              </div>
            </div>
          </div>
          <input
            class="modal-seek"
            type="range"
            min="0"
            :max="duration || 0"
            step="0.1"
            :value="currentTime"
            :disabled="!duration"
            @input="seekAudioRange"
          />
        </div>
      </div>
    </div>

    <div v-if="showRelatedVideoModal" class="score-modal" @click.self="closeRelatedVideoModal">
      <div class="score-modal-content related-video-modal-content">
        <div class="score-modal-header">
          <span>{{ activeRelatedVideo?.title || '相关学习视频' }}</span>
          <div class="score-modal-actions">
            <a
              v-if="activeRelatedVideo"
              class="ghost-link"
              :href="buildRelatedVideoUrl(activeRelatedVideo)"
              target="_blank"
              rel="noreferrer"
            >
              打开原视频
            </a>
            <button class="ghost-btn" @click="closeRelatedVideoModal">关闭</button>
          </div>
        </div>

        <div class="video-frame related-video-frame" v-if="activeRelatedVideo">
          <video :src="buildRelatedVideoUrl(activeRelatedVideo)" controls autoplay playsinline />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { loadLocalSeedIndex } from '../utils/localSeedIndex'

const COACH_MODEL_STORAGE_KEY = 'guitar-platform-coach-model'
const PENDING_COURSE_ID_KEY = 'guitar-platform-pending-course-id'
const PENDING_VIDEO_ID_KEY = 'guitar-platform-pending-video-id'
const PENDING_SONG_ID_KEY = 'guitar-platform-pending-song-id'
const LEARNING_PLAN_PROGRESS_KEY = 'guitar-platform-learning-plan-progress'
const LEARNING_ROUND_HISTORY_KEY = 'guitar-platform-learning-round-history'
const PRACTICE_SIDE_TAB_STORAGE_KEY = 'guitar-platform-practice-side-tab'
const LOOP_SNIPPETS_STORAGE_KEY = 'guitar-platform-loop-snippets'
const RECENT_PRACTICE_LINKS_KEY = 'guitar-platform-recent-practice-links'
const BACKING_VOLUME_STORAGE_KEY = 'guitar-platform-backing-volume'
const COACH_MODELS = [
  { value: 'qwen3:8b', label: 'Qwen 3 8B', hint: '更稳，更像日常陪练' },
  { value: 'deepseek-r1:8b', label: 'DeepSeek R1 8B', hint: '推理更强，建议更展开' },
]

export default {
  name: 'SongsView',
  data() {
    return {
      songs: [],
      loading: false,
      selectedSong: null,
      selectedVersion: '',
      selectedVersionFiles: {},
      searchQuery: '',
      audio: null,
      isPlaying: false,
      currentTime: 0,
      duration: 0,
      playbackRate: 1,
      backingVolume: this.loadBackingVolume(),
      speeds: [0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0],
      loopStart: null,
      loopEnd: null,
      showScoreModal: false,
      scoreType: 'pdf',
      scoreUrl: '',
      pdfDoc: null,
      gpApi: null,
      gpLoading: false,
      gpError: '',
      scoreNotice: '',
      recordingSupported: false,
      mediaRecorder: null,
      mixRecorder: null,
      mediaStream: null,
      analysisStream: null,
      recordedChunks: [],
      mixedChunks: [],
      isRecording: false,
      coachPlaybackActive: false,
      videoCoachActive: false,
      coachAnalyzing: false,
      coachError: '',
      coachResult: null,
      coachRecordingStartedAt: 0,
      coachRecordingDuration: 0,
      coachCaptureMode: 'audio',
      coachCountdown: 0,
      coachCountdownTimer: null,
      coachRecordingUrl: '',
      pendingCoachTake: null,
      coachPlaybackAudio: null,
      coachPlaybackStopTimer: null,
      coachCompareToken: 0,
      coachHistory: [],
      selectedCoachSessionIds: [],
      lastSavedCoachSessionId: '',
      relatedVideos: [],
      relatedVideosLoading: false,
      showRelatedVideoModal: false,
      activeRelatedVideo: null,
      learningRecommendations: null,
      learningRecommendationsLoading: false,
      learningPlanProgress: this.loadLearningPlanProgress(),
      learningRoundHistory: this.loadLearningRoundHistory(),
      coachModels: COACH_MODELS,
      coachModel: this.loadCoachModel(),
	      practiceSideTab: this.loadPracticeSideTab(),
	      playbackMode: 'normal',
	      selectedAudioFile: '',
	      loopSnippetDraft: '',
	      loopSnippets: this.loadLoopSnippets(),
	      recentPracticeLinks: this.loadRecentPracticeLinks(),
      audioContext: null,
      mixDestination: null,
      backingSourceNode: null,
      backingMonitorGain: null,
      backingRecordGain: null,
      inputRecordGain: null,
      currentInputSource: null,
	    }
  },
  computed: {
    currentAudioFile() {
      return this.selectedAudioFile || this.selectedVersionFiles.audio || ''
    },
    audioOptions() {
      const options = this.selectedVersionFiles.audio_options || []
      return options.map(path => ({
        path,
        label: this.audioOptionLabel(path),
      }))
    },
    currentLoopSnippetKey() {
      if (!this.selectedSong?.id || !this.currentAudioFile) return ''
      return `${this.selectedSong.id}::${this.currentAudioFile}`
    },
    currentLoopSnippets() {
      if (!this.currentLoopSnippetKey) return []
      return this.loopSnippets[this.currentLoopSnippetKey] || []
    },
    activeLoopSnippet() {
      if (this.loopStart === null || this.loopEnd === null) return null
      return this.currentLoopSnippets.find(
        snippet => Math.abs(snippet.start - this.loopStart) < 0.05 && Math.abs(snippet.end - this.loopEnd) < 0.05,
      ) || null
    },
    currentAudioLabel() {
      return this.currentAudioFile ? this.audioOptionLabel(this.currentAudioFile) : '未选择伴奏'
    },
    siblingLoopSnippetGroups() {
      if (!this.selectedSong?.id) return []
      return this.audioOptions
        .filter(option => option.path !== this.currentAudioFile)
        .map(option => ({
          path: option.path,
          label: option.label,
          snippets: this.loopSnippets[`${this.selectedSong.id}::${option.path}`] || [],
        }))
        .filter(group => group.snippets.length)
    },
    filteredSongs() {
      const keyword = this.searchQuery.trim().toLowerCase()
      if (!keyword) return this.songs
      return this.songs.filter(song => {
        const haystacks = [
          song.title,
          song.artist,
          ...(song.versions || []),
        ]
        return haystacks.some(value => (value || '').toLowerCase().includes(keyword))
      })
    },
    progressPercent() {
      if (!this.duration) return 0
      return Math.min((this.currentTime / this.duration) * 100, 100)
    },
    backingVolumePercent() {
      return Math.round(this.backingVolume * 100)
    },
    visibleMarkers() {
      if (!this.selectedSong || !this.selectedVersion) return []
      return (this.selectedSong.markers || []).filter(marker => marker.version === this.selectedVersion)
    },
    versionGroups() {
      if (!this.selectedSong?.versions?.length) return []
      const groups = new Map()

      this.selectedSong.versions.forEach(version => {
        const segments = version.name.split(' / ').map(part => part.trim()).filter(Boolean)
        const groupName = segments[0] || version.name

        if (!groups.has(groupName)) {
          groups.set(groupName, { name: groupName, root: null, segments: [] })
        }

        const group = groups.get(groupName)
        if (segments.length <= 1 || version.name === '默认版') {
          group.root = version
        } else {
          group.segments.push(version)
        }
      })

      return Array.from(groups.values())
    },
    currentGroupName() {
      if (!this.selectedVersion) return ''
      return this.selectedVersion.split(' / ')[0]
    },
    currentVersionGroup() {
      if (!this.currentGroupName) return null
      return this.versionGroups.find(group => group.name === this.currentGroupName) || null
    },
    currentVersionOptionCount() {
      if (!this.currentVersionGroup) return 0
      return (this.currentVersionGroup.root ? 1 : 0) + (this.currentVersionGroup.segments?.length || 0)
    },
    showVersionGroups() {
      return this.versionGroups.length > 1
    },
    showStandaloneVersions() {
      if (!this.selectedSong?.versions?.length) return false
      if (this.currentVersionGroup?.segments?.length) return false
      return this.versionGroups.length <= 1
    },
    referenceFiles() {
      const group = this.currentVersionGroup
      return group?.root?.files || {}
    },
    currentCoachModelHint() {
      const active = this.coachModels.find(item => item.value === this.coachModel)
      return active ? `当前模型：${active.label} · ${active.hint}` : `当前模型：${this.coachModel}`
    },
    hasSelectedCoachSessions() {
      return this.selectedVisibleCoachSessionIds.length > 0
    },
    visibleCoachHistory() {
      if (!this.selectedSong?.id) return []
      return this.coachHistory.filter(session => session.song_id === this.selectedSong.id)
    },
    selectedVisibleCoachSessionIds() {
      const visibleIds = new Set(this.visibleCoachHistory.map(session => session.session_id))
      return this.selectedCoachSessionIds.filter(id => visibleIds.has(id))
    },
    currentPlanChecklist() {
      return this.learningRecommendations?.today_plan?.checklist || []
    },
    currentPlanCheckedCount() {
      if (!this.selectedSong?.id) return 0
      const completed = this.learningPlanProgress[this.selectedSong.id] || []
      return this.currentPlanChecklist.filter((_, index) => completed.includes(index)).length
    },
    currentPathStepCount() {
      return this.learningRecommendations?.learning_path?.length || 0
    },
    currentPathDoneCount() {
      return (this.learningRecommendations?.learning_path || []).filter(
        step => this.pathStatusLabel(step.step) === '已完成',
      ).length
    },
    learningFlowCompleted() {
      if (!this.currentPlanChecklist.length) return false
      return this.currentPlanCheckedCount === this.currentPlanChecklist.length
    },
    currentRoundSummary() {
      if (!this.selectedSong?.id) return null
      const summary = this.learningRoundHistory[this.selectedSong.id]
      if (!summary) return null
      return {
        roundsToday: summary.date === this.currentPracticeDateKey() ? summary.roundsToday || 0 : 0,
        totalRounds: summary.totalRounds || 0,
        lastCompletedAt: summary.lastCompletedAt || '',
      }
    },
    todayPracticeSummary() {
      const todayKey = this.currentPracticeDateKey()
      return Object.entries(this.learningRoundHistory)
        .map(([songId, summary]) => {
          if (!summary || summary.date !== todayKey || !summary.roundsToday) return null
          const song = this.songs.find(item => item.id === songId)
          return {
            songId,
            title: song?.title || songId,
            roundsToday: summary.roundsToday || 0,
            totalRounds: summary.totalRounds || 0,
            lastCompletedAt: summary.lastCompletedAt || '',
          }
        })
        .filter(Boolean)
        .sort((a, b) => new Date(b.lastCompletedAt).getTime() - new Date(a.lastCompletedAt).getTime())
    },
    currentPathProgress() {
      if (!this.selectedSong?.id) return {}
      return this.learningPlanProgress[`${this.selectedSong.id}::path`] || {}
    },
    coachStatusText() {
      if (this.coachAnalyzing) return '正在保存这次录制和练习回放'
      if (this.pendingCoachTake) return '这次录制先别急着分析，先听预览，满意后再 Save，不满意就 Retry。'
      if (this.videoCoachActive) return '音画同录中，正在同步录像、录音与伴奏'
      if (this.coachPlaybackActive) return '内录混音中，正在同步录音与伴奏'
      if (this.isRecording) return this.coachCaptureMode === 'video' ? '录像录音中，请完整弹完当前练习段落' : '录音中，请完整弹完当前练习段落'
      if (this.coachResult) return '本次练习回放已生成，可以直接保存、下载或继续下一遍。'
      return '建议把系统默认输入切到 Scarlett 2i2；如果要录视频，可直接用音画同录。'
    },
    playbackButtonLabel() {
      if (this.videoCoachActive) return '停止音画同录'
      if (this.coachPlaybackActive) return '停止内录混音'
      if (this.playbackMode === 'video') return '开始音画同录'
      if (this.playbackMode === 'mix') return '开始内录混音'
      return this.isPlaying ? '停止播放' : '开始播放'
    },
    currentPlaybackModeLabel() {
      return {
        normal: '当前模式：正常播放',
        mix: '当前模式：内录混音',
        video: '当前模式：音画同录',
      }[this.playbackMode] || '当前模式：正常播放'
    },
    playbackModeDescription() {
      if (this.playbackMode === 'video') return '点红点后倒计时 3 秒，再自动播放伴奏并开始录像录音。'
      if (this.playbackMode === 'mix') return '点红点后直接开始伴奏与吉他输入的内录混音。'
      return '正常听伴奏练习，不录音也不录像。'
    },
    coachPrimaryIssue() {
      return this.coachResult?.issues?.[0]?.message || ''
    },
    coachPrimaryAdvice() {
      return this.coachResult?.advice?.[0] || ''
    },
    hasPendingCoachTake() {
      return Boolean(this.pendingCoachTake)
    },
    playbackButtonIcon() {
      if (this.videoCoachActive || this.coachPlaybackActive || this.isPlaying) return '■'
      if (this.playbackMode === 'video' || this.playbackMode === 'mix') return '●'
      return '▶'
    },
    playbackButtonTone() {
      if (this.playbackMode === 'video' || this.playbackMode === 'mix' || this.videoCoachActive || this.coachPlaybackActive) {
        return 'record-mode'
      }
      return 'normal-mode'
    },
  },
  watch: {
    learningFlowCompleted(isComplete) {
      this.syncLearningFlowRound(isComplete)
    },
  },
  async mounted() {
    this.recordingSupported = Boolean(
      window?.navigator?.mediaDevices?.getUserMedia && window.MediaRecorder,
    )
    window.addEventListener('guitar-platform-coach-model-change', this.handleCoachModelChange)
    this.initAudio()
    await this.loadSongs()
    await this.loadCoachSessions()
  },
  beforeUnmount() {
    window.removeEventListener('guitar-platform-coach-model-change', this.handleCoachModelChange)
    if (this.audio) {
      this.audio.pause()
      this.audio.src = ''
    }
    this.clearCoachCountdown()
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop()
    }
    this.clearCoachRecordingPreview()
    this.stopCoachSegmentPlayback()
    this.stopCoachStream()
    this.destroyGpApi()
  },
  methods: {
    initAudio() {
      this.audio = new Audio()
      this.audio.volume = this.backingVolume
      this.audio.addEventListener('timeupdate', () => {
        this.currentTime = this.audio.currentTime
        if (
          this.loopStart !== null
          && this.loopEnd !== null
          && this.loopEnd > this.loopStart
          && this.audio.currentTime >= this.loopEnd
        ) {
          if (this.videoCoachActive) {
            this.stopVideoCoachPlayback()
            return
          }
          if (this.coachPlaybackActive) {
            this.stopCoachPlayback()
            return
          }
          this.audio.currentTime = this.loopStart
        }
      })
      this.audio.addEventListener('loadedmetadata', () => {
        this.duration = this.audio.duration || 0
      })
      this.audio.addEventListener('play', () => {
        this.isPlaying = true
      })
      this.audio.addEventListener('pause', () => {
        this.isPlaying = false
      })
      this.audio.addEventListener('ended', () => {
        this.isPlaying = false
        if (this.videoCoachActive && this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
          this.stopVideoCoachPlayback()
          return
        }
        if (this.coachPlaybackActive && this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
          this.stopCoachPlayback()
        }
      })
      this.applyBackingVolume()
    },
    async loadSongs() {
      this.loading = true
      try {
        const response = await fetch('/api/songs')
        if (!response.ok) throw new Error('歌曲列表加载失败')
        this.songs = await response.json()
      } catch (error) {
        const seedIndex = await loadLocalSeedIndex()
        this.songs = seedIndex.songs.map(song => ({
          id: song.id,
          title: song.title,
          artist: song.artist || '',
          versions: song.versions.map(version => version.name),
        }))
      } finally {
        const pendingSongId = this.consumePendingSongId()
        if (pendingSongId) {
          const pendingSong = this.songs.find(item => item.id === pendingSongId)
          if (pendingSong) {
            await this.selectSong(pendingSong)
            this.loading = false
            return
          }
        }
        if (!this.selectedSong && this.songs.length) {
          await this.selectSong(this.songs[0])
        }
        this.loading = false
      }
    },
    async scanSongs() {
      this.loading = true
      try {
        await fetch('/api/songs/scan?persist=true')
        await this.loadSongs()
      } finally {
        this.loading = false
      }
    },
    async selectSong(song) {
      this.stopAudio()
      this.closeRelatedVideoModal()
      this.lastSavedCoachSessionId = ''
      this.loopSnippetDraft = ''
      try {
        const response = await fetch(`/api/songs/${song.id}`)
        if (!response.ok) throw new Error('歌曲详情加载失败')
        this.selectedSong = await response.json()
      } catch {
        const seedIndex = await loadLocalSeedIndex()
        this.selectedSong = seedIndex.songs.find(item => item.id === song.id) || null
      }
      if (!this.selectedSong) return
      this.selectedCoachSessionIds = []
      await this.loadLearningRecommendations(this.selectedSong.id)
      await this.loadRelatedVideos(this.selectedSong.id)
      if (this.selectedSong.versions?.length) {
        this.selectVersion(this.selectedSong.versions[0])
      }
    },
    async loadLearningRecommendations(songId) {
      this.learningRecommendationsLoading = true
      try {
        const response = await fetch(`/api/coach/recommendations?song_id=${encodeURIComponent(songId)}`)
        if (!response.ok) throw new Error('学习建议加载失败')
        this.learningRecommendations = await response.json()
      } catch (error) {
        console.warn(error)
        this.learningRecommendations = null
      } finally {
        this.learningRecommendationsLoading = false
      }
    },
    async loadRelatedVideos(songId) {
      this.relatedVideosLoading = true
      try {
        const response = await fetch(`/api/songs/${songId}/related-videos`)
        if (!response.ok) throw new Error('相关学习视频加载失败')
        this.relatedVideos = await response.json()
      } catch (error) {
        console.warn(error)
        this.relatedVideos = []
      } finally {
        this.relatedVideosLoading = false
      }
    },
    async deleteSelectedSong() {
      if (!this.selectedSong || this.loading || this.isFilePreview()) return
      const confirmed = window.confirm(`确定删除歌曲“${this.selectedSong.title}”吗？该歌曲目录里的谱、伴奏和参考资料会一起删除。`)
      if (!confirmed) return

      this.loading = true
      const currentId = this.selectedSong.id
      try {
        const response = await fetch(`/api/songs/${currentId}`, { method: 'DELETE' })
        const data = await response.json()
        if (!response.ok) throw new Error(data.detail || '删除失败')

        this.stopAudio()
        this.closeScoreModal()
        this.songs = data.songs || []
        this.selectedSong = null
        this.selectedVersion = ''
        this.selectedVersionFiles = {}

        const fallback = this.songs.find(song => song.id !== currentId) || this.songs[0] || null
        if (fallback) {
          await this.selectSong(fallback)
        }
      } catch (error) {
        window.alert(error.message || '删除失败')
      } finally {
        this.loading = false
      }
    },
    selectVersion(version) {
      this.selectedVersion = version.name
      this.selectedVersionFiles = version.files || {}
      this.selectedAudioFile = (version.files?.audio_options && version.files.audio_options[0]) || version.files?.audio || ''
      this.loopSnippetDraft = ''
      this.loopStart = null
      this.loopEnd = null
      this.resetCoachResult()
      this.stopAudio()
      if (this.currentAudioFile) {
        this.audio.src = this.buildSongMediaUrl(this.currentAudioFile)
        this.audio.load()
        this.audio.playbackRate = this.playbackRate
      }
    },
    selectVersionGroup(group) {
      if (group.segments?.length) {
        this.selectVersion(group.segments[0])
        return
      }

      if (group.root) {
        this.selectVersion(group.root)
      }
    },
    async togglePlay() {
      if (!this.currentAudioFile) return
      if (this.audio.paused) {
        this.rememberCurrentPractice()
        this.audio.currentTime = this.playbackStartTime()
        await this.audio.play()
      } else {
        this.audio.pause()
      }
    },
    async handlePlaybackAction() {
      if (!this.currentAudioFile || this.coachAnalyzing || this.hasPendingCoachTake) return
      if (this.videoCoachActive) {
        this.stopVideoCoachPlayback()
        return
      }
      if (this.coachPlaybackActive) {
        this.stopCoachPlayback()
        return
      }
      if (this.playbackMode === 'video') {
        await this.startVideoCoachPlayback()
        return
      }
      if (this.playbackMode === 'mix') {
        await this.startCoachPlayback()
        return
      }
      await this.togglePlay()
    },
    async startCoachPlayback() {
      if (!this.currentAudioFile || this.coachAnalyzing || this.coachPlaybackActive) return
      this.rememberCurrentPractice()
      await this.startCoachRecording({ autoplay: true, withVideo: false })
    },
    async startVideoCoachPlayback() {
      if (!this.currentAudioFile || this.coachAnalyzing || this.videoCoachActive) return
      this.rememberCurrentPractice()
      await this.startCoachRecording({ autoplay: true, withVideo: true, countdown: 3 })
    },
    stopCoachPlayback() {
      if (!this.coachPlaybackActive) return
      this.coachPlaybackActive = false
      if (this.audio && !this.audio.paused) {
        this.audio.pause()
      }
      if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') this.mediaRecorder.stop()
      if (this.mixRecorder && this.mixRecorder.state !== 'inactive') this.mixRecorder.stop()
      this.isRecording = false
      this.coachRecordingDuration = Math.max(0, (Date.now() - this.coachRecordingStartedAt) / 1000)
      this.clearCoachCountdown()
      this.videoCoachActive = false
      this.coachCaptureMode = 'audio'
    },
    stopVideoCoachPlayback() {
      if (!this.videoCoachActive) return
      this.videoCoachActive = false
      if (this.audio && !this.audio.paused) {
        this.audio.pause()
      }
      if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') this.mediaRecorder.stop()
      if (this.mixRecorder && this.mixRecorder.state !== 'inactive') this.mixRecorder.stop()
      this.isRecording = false
      this.coachRecordingDuration = Math.max(0, (Date.now() - this.coachRecordingStartedAt) / 1000)
      this.clearCoachCountdown()
      this.coachPlaybackActive = false
      this.coachCaptureMode = 'video'
    },
    stopAudio() {
      if (!this.audio) return
      this.audio.pause()
      this.audio.currentTime = 0
      this.currentTime = 0
      this.duration = 0
    },
    seekAudio(event) {
      if (!this.duration) return
      const rect = event.currentTarget.getBoundingClientRect()
      const percent = (event.clientX - rect.left) / rect.width
      this.audio.currentTime = Math.max(0, Math.min(this.duration, percent * this.duration))
    },
    seekAudioRange(event) {
      if (!this.audio || !this.duration) return
      this.audio.currentTime = Math.max(0, Math.min(this.duration, Number(event.target.value)))
    },
    setSpeed(speed) {
      this.playbackRate = speed
      if (this.audio) {
        this.audio.playbackRate = speed
      }
    },
    loadBackingVolume() {
      try {
        const raw = Number(window.localStorage.getItem(BACKING_VOLUME_STORAGE_KEY))
        if (Number.isFinite(raw) && raw >= 0 && raw <= 1.5) {
          return raw
        }
      } catch {}
      return 0.9
    },
    persistBackingVolume() {
      try {
        window.localStorage.setItem(BACKING_VOLUME_STORAGE_KEY, String(this.backingVolume))
      } catch {}
    },
    setBackingVolume(event) {
      const value = Number(event?.target?.value)
      if (!Number.isFinite(value)) return
      this.backingVolume = Math.max(0, Math.min(1.5, value / 100))
      this.applyBackingVolume()
      this.persistBackingVolume()
    },
    applyBackingVolume() {
      if (this.audio) {
        this.audio.volume = this.backingVolume
      }
      if (this.backingMonitorGain) {
        this.backingMonitorGain.gain.value = this.backingVolume
      }
      if (this.backingRecordGain) {
        this.backingRecordGain.gain.value = this.backingVolume * 0.92
      }
    },
    setLoopStart() {
      this.loopStart = this.clampAudioTime(this.audio.currentTime)
      if (this.loopEnd !== null && this.loopEnd <= this.loopStart) {
        this.loopEnd = null
      }
    },
    setLoopEnd() {
      const end = this.clampAudioTime(this.audio.currentTime)
      if (this.loopStart !== null && end <= this.loopStart) {
        this.loopStart = Math.max(0, end - 0.5)
      }
      this.loopEnd = end
    },
    clearLoop() {
      this.loopStart = null
      this.loopEnd = null
    },
    loadLoopSnippets() {
      try {
        return JSON.parse(window.localStorage.getItem(LOOP_SNIPPETS_STORAGE_KEY) || '{}')
      } catch {
        return {}
      }
    },
    persistLoopSnippets() {
      try {
        window.localStorage.setItem(LOOP_SNIPPETS_STORAGE_KEY, JSON.stringify(this.loopSnippets))
      } catch {}
    },
    loadRecentPracticeLinks() {
      try {
        return JSON.parse(window.localStorage.getItem(RECENT_PRACTICE_LINKS_KEY) || '[]')
      } catch {
        return []
      }
    },
    persistRecentPracticeLinks() {
      try {
        window.localStorage.setItem(RECENT_PRACTICE_LINKS_KEY, JSON.stringify(this.recentPracticeLinks))
      } catch {}
    },
    rememberCurrentPractice() {
      if (!this.selectedSong?.id || !this.selectedVersion || !this.currentAudioFile) return
      const activeLoop = this.activeLoopSnippet
      const entry = {
        id: `${this.selectedSong.id}::${this.selectedVersion}::${this.currentAudioFile}`,
        songId: this.selectedSong.id,
        songTitle: this.selectedSong.title,
        version: this.selectedVersion,
        audioPath: this.currentAudioFile,
        audioLabel: this.currentAudioLabel,
        playbackRate: this.playbackRate,
        loopSnippetId: activeLoop?.id || '',
        loopLabel: activeLoop?.label || (this.loopStart !== null && this.loopEnd !== null ? `${this.formatTime(this.loopStart)} - ${this.formatTime(this.loopEnd)}` : ''),
        loopStart: this.loopStart,
        loopEnd: this.loopEnd,
        updatedAt: new Date().toISOString(),
      }
      this.recentPracticeLinks = [
        entry,
        ...this.recentPracticeLinks.filter(item => item.id !== entry.id),
      ].slice(0, 3)
      this.persistRecentPracticeLinks()
    },
    async openRecentPractice(item) {
      const song = this.songs.find(entry => entry.id === item.songId)
      if (!song) return
      await this.selectSong(song)
      const targetVersion = (this.selectedSong?.versions || []).find(version => version.name === item.version)
      if (targetVersion) {
        this.selectVersion(targetVersion)
      }
      if (item.audioPath) {
        this.selectAudioOption(item.audioPath)
      }
      this.playbackRate = item.playbackRate || 1
      if (this.audio) {
        this.audio.playbackRate = this.playbackRate
      }
      if (Number.isFinite(item.loopStart) && Number.isFinite(item.loopEnd)) {
        this.loopStart = this.clampAudioTime(item.loopStart)
        this.loopEnd = this.clampAudioTime(item.loopEnd)
        this.audio.currentTime = this.loopStart
        this.currentTime = this.loopStart
      }
    },
    saveCurrentLoopSnippet() {
      if (!this.currentLoopSnippetKey || this.loopStart === null || this.loopEnd === null || !this.loopSnippetDraft) return
      const nextSnippet = {
        id: `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`,
        label: this.loopSnippetDraft,
        start: Number(this.loopStart.toFixed(2)),
        end: Number(this.loopEnd.toFixed(2)),
      }
      this.loopSnippets = {
        ...this.loopSnippets,
        [this.currentLoopSnippetKey]: [...this.currentLoopSnippets, nextSnippet].sort((a, b) => a.start - b.start),
      }
      this.persistLoopSnippets()
      this.loopSnippetDraft = ''
    },
    applyLoopSnippet(snippet) {
      this.loopStart = this.clampAudioTime(snippet.start)
      this.loopEnd = this.clampAudioTime(snippet.end)
      this.audio.currentTime = this.loopStart
      this.currentTime = this.loopStart
    },
    deleteLoopSnippet(snippetId) {
      if (!this.currentLoopSnippetKey) return
      const nextItems = this.currentLoopSnippets.filter(item => item.id !== snippetId)
      this.loopSnippets = {
        ...this.loopSnippets,
        [this.currentLoopSnippetKey]: nextItems,
      }
      if (!nextItems.length) {
        const { [this.currentLoopSnippetKey]: _removed, ...rest } = this.loopSnippets
        this.loopSnippets = rest
      }
      this.persistLoopSnippets()
    },
    seekToTime(time) {
      this.audio.currentTime = time
      if (this.audio.paused) {
        this.audio.play().catch(() => {})
      }
    },
    playbackStartTime() {
      if (this.loopStart !== null) {
        return this.clampAudioTime(this.loopStart)
      }
      return this.clampAudioTime(this.audio?.currentTime || 0)
    },
    clampAudioTime(time) {
      const value = Number.isFinite(time) ? time : 0
      if (!this.duration) return Math.max(0, value)
      return Math.max(0, Math.min(this.duration, value))
    },
    formatTime(seconds) {
      if (!Number.isFinite(seconds)) return '0:00'
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins}:${secs.toString().padStart(2, '0')}`
    },
    gridColumnsStyle(count, maxColumns = 5) {
      const columns = Math.max(1, Math.min(Number(count) || 1, maxColumns))
      return { gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }
    },
    versionSummary(version) {
      const files = []
      if (version.files?.audio_options?.length) {
        files.push(`${version.files.audio_options.length} 个音频`)
      } else if (version.files?.audio) {
        files.push('伴奏')
      }
      if (version.files?.pdf) files.push('PDF')
      if (version.files?.gp) files.push('GP')
      if (version.files?.video) files.push('视频')
      if (version.files?.image) files.push('图片')
      return files.join(' / ') || '无媒体'
    },
    versionLeafLabel(versionName) {
      const parts = versionName.split(' / ')
      return parts[parts.length - 1]
    },
    groupSummary(group) {
      const parts = []
      if (group.root) {
        parts.push(`整版 ${this.versionSummary(group.root)}`)
      }
      if (group.segments.length) {
        parts.push(`${group.segments.length} 个段落`)
      }
      return parts.join(' · ')
    },
    buildSongMediaUrl(file) {
      const path = `${this.selectedSong.path}/${file}`
      const cleanPath = path.split('/').map(encodeURIComponent).join('/')
      return this.isFilePreview()
        ? `file:///Users/m5air/GuitarPlatform_v2/library/songs/${cleanPath}`
        : `/api/songs/${this.selectedSong.id}/asset?path=${encodeURIComponent(file)}`
    },
    audioOptionLabel(path) {
      const fileName = path.split('/').pop() || path
      return fileName.replace(/\.[^.]+$/, '').trim()
    },
    selectAudioOption(path) {
      if (!path || path === this.selectedAudioFile) return
      const wasPlaying = this.audio && !this.audio.paused
      this.stopAudio()
      this.selectedAudioFile = path
      this.loopSnippetDraft = ''
      this.loopStart = null
      this.loopEnd = null
      if (this.currentAudioFile) {
        this.audio.src = this.buildSongMediaUrl(this.currentAudioFile)
        this.audio.load()
        this.audio.playbackRate = this.playbackRate
        if (wasPlaying) {
          this.audio.play().catch(() => {})
        }
      }
    },
    buildRelatedVideoUrl(video) {
      return `/api/videos/${video.id}/stream`
    },
    buildRelatedVideoThumbnailUrl(video) {
      return `/api/videos/${video.id}/thumbnail`
    },
    navigateToTab(tab, payload = {}) {
      if (tab === 'courses' && payload.courseId) {
        window.localStorage.setItem(PENDING_COURSE_ID_KEY, payload.courseId)
      }
      if (tab === 'learning' && payload.videoId) {
        window.localStorage.setItem(PENDING_VIDEO_ID_KEY, payload.videoId)
      }
      if (tab === 'songs' && payload.songId) {
        window.localStorage.setItem(PENDING_SONG_ID_KEY, payload.songId)
      }
      window.dispatchEvent(new CustomEvent('guitar-platform-navigate', { detail: { tab } }))
    },
    consumePendingSongId() {
      try {
        const pending = window.localStorage.getItem(PENDING_SONG_ID_KEY) || ''
        if (pending) {
          window.localStorage.removeItem(PENDING_SONG_ID_KEY)
        }
        return pending
      } catch {
        return ''
      }
    },
    loadLearningPlanProgress() {
      try {
        return JSON.parse(window.localStorage.getItem(LEARNING_PLAN_PROGRESS_KEY) || '{}')
      } catch {
        return {}
      }
    },
    loadLearningRoundHistory() {
      try {
        return JSON.parse(window.localStorage.getItem(LEARNING_ROUND_HISTORY_KEY) || '{}')
      } catch {
        return {}
      }
    },
    persistLearningPlanProgress() {
      window.localStorage.setItem(LEARNING_PLAN_PROGRESS_KEY, JSON.stringify(this.learningPlanProgress))
    },
    persistLearningRoundHistory() {
      window.localStorage.setItem(LEARNING_ROUND_HISTORY_KEY, JSON.stringify(this.learningRoundHistory))
    },
    currentPracticeDateKey() {
      const now = new Date()
      const year = now.getFullYear()
      const month = `${now.getMonth() + 1}`.padStart(2, '0')
      const day = `${now.getDate()}`.padStart(2, '0')
      return `${year}-${month}-${day}`
    },
    formatRoundTimestamp(value) {
      if (!value) return ''
      const date = new Date(value)
      if (Number.isNaN(date.getTime())) return ''
      return `${`${date.getHours()}`.padStart(2, '0')}:${`${date.getMinutes()}`.padStart(2, '0')}`
    },
    syncLearningFlowRound(isComplete) {
      if (!this.selectedSong?.id || !this.currentPlanChecklist.length) return
      const songId = this.selectedSong.id
      const markerKey = `${songId}::flow-recorded`
      const marker = Boolean(this.learningPlanProgress[markerKey])

      if (isComplete && !marker) {
        const now = new Date().toISOString()
        const dateKey = this.currentPracticeDateKey()
        const previous = this.learningRoundHistory[songId] || {}
        const roundsToday = previous.date === dateKey ? (previous.roundsToday || 0) + 1 : 1

        this.learningRoundHistory = {
          ...this.learningRoundHistory,
          [songId]: {
            date: dateKey,
            roundsToday,
            totalRounds: (previous.totalRounds || 0) + 1,
            lastCompletedAt: now,
          },
        }
        this.learningPlanProgress = {
          ...this.learningPlanProgress,
          [markerKey]: true,
        }
        this.persistLearningRoundHistory()
        this.persistLearningPlanProgress()
        return
      }

      if (!isComplete && marker) {
        this.learningPlanProgress = {
          ...this.learningPlanProgress,
          [markerKey]: false,
        }
        this.persistLearningPlanProgress()
      }
    },
    isPlanItemCompleted(index) {
      if (!this.selectedSong?.id) return false
      return (this.learningPlanProgress[this.selectedSong.id] || []).includes(index)
    },
    togglePlanItem(index) {
      if (!this.selectedSong?.id) return
      const songId = this.selectedSong.id
      const current = new Set(this.learningPlanProgress[songId] || [])
      if (current.has(index)) {
        current.delete(index)
      } else {
        current.add(index)
      }
      const pathKey = `${songId}::path`
      const pathProgress = { ...(this.learningPlanProgress[pathKey] || {}) }
      const step = this.findPathStepByChecklistIndex(index)
      if (step) {
        pathProgress[String(step.step)] = current.has(index) ? 'done' : 'todo'
      }
      this.learningPlanProgress = {
        ...this.learningPlanProgress,
        [songId]: Array.from(current).sort((a, b) => a - b),
        [pathKey]: pathProgress,
      }
      this.persistLearningPlanProgress()
    },
    stepChecklistIndex(stepNumber) {
      const step = (this.learningRecommendations?.learning_path || []).find(item => item.step === stepNumber)
      if (!step) return null
      if (step.type === 'song') return 0
      if (step.type === 'course') return 1
      if (step.type === 'video') return 2
      if (step.type === 'verify') return 3
      return null
    },
    findPathStepByChecklistIndex(index) {
      return (this.learningRecommendations?.learning_path || []).find(step => this.stepChecklistIndex(step.step) === index) || null
    },
    pathStatusLabel(stepNumber) {
      const status = this.currentPathProgress[String(stepNumber)] || 'todo'
      return {
        todo: '待开始',
        doing: '进行中',
        done: '已完成',
      }[status] || '待开始'
    },
    pathStatusActionLabel(stepNumber) {
      const status = this.currentPathProgress[String(stepNumber)] || 'todo'
      return {
        todo: '标记开始',
        doing: '标记完成',
        done: '重置状态',
      }[status] || '标记开始'
    },
    cyclePathStatus(stepNumber) {
      if (!this.selectedSong?.id) return
      const songId = this.selectedSong.id
      const pathKey = `${this.selectedSong.id}::path`
      const current = { ...(this.learningPlanProgress[pathKey] || {}) }
      const key = String(stepNumber)
      const now = current[key] || 'todo'
      const next = now === 'todo' ? 'doing' : now === 'doing' ? 'done' : 'todo'
      current[key] = next
      const planIndex = this.stepChecklistIndex(stepNumber)
      const completed = new Set(this.learningPlanProgress[songId] || [])
      if (planIndex !== null) {
        if (next === 'done') {
          completed.add(planIndex)
        } else if (next === 'todo') {
          completed.delete(planIndex)
        }
      }
      this.learningPlanProgress = {
        ...this.learningPlanProgress,
        [pathKey]: current,
        [songId]: Array.from(completed).sort((a, b) => a - b),
      }
      this.persistLearningPlanProgress()
    },
    openRecommendedCourse(course) {
      if (!course?.id) return
      this.navigateToTab('courses', { courseId: course.id })
    },
    openRecommendedVideo(video) {
      if (!video?.id) return
      const matched = this.relatedVideos.find(item => item.id === video.id)
      if (matched) {
        this.openRelatedVideo(matched)
        return
      }
      this.navigateToTab('learning', { videoId: video.id })
    },
    openRelatedVideo(video) {
      this.activeRelatedVideo = video
      this.showRelatedVideoModal = true
    },
    closeRelatedVideoModal() {
      this.showRelatedVideoModal = false
      this.activeRelatedVideo = null
    },
    async openTodayPracticeSong(songId) {
      const target = this.songs.find(song => song.id === songId)
      if (!target) return
      await this.selectSong(target)
    },
    isFilePreview() {
      return window.location.protocol === 'file:'
    },
    async addMarker() {
      if (!this.selectedSong || !this.selectedVersion) return
      const label = window.prompt('输入标记名称')
      if (!label) return

      const response = await fetch(`/api/songs/${this.selectedSong.id}/markers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          time: this.audio.currentTime,
          label,
          version: this.selectedVersion,
        }),
      })

      if (!response.ok) return
      const data = await response.json()
      this.selectedSong.markers = [...(this.selectedSong.markers || []), data.marker]
    },
    async startCoachRecording(options = {}) {
      if (!this.recordingSupported) {
        this.coachError = '当前浏览器不支持录音，请在 MacBook 本地浏览器中打开平台。'
        return
      }
      if (!this.selectedSong || !this.selectedVersion) return

      this.coachError = ''
      this.coachResult = null
      this.coachRecordingDuration = 0
      this.pendingCoachTake = null
      this.clearCoachRecordingPreview()

      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: false,
            noiseSuppression: false,
            autoGainControl: false,
            channelCount: 2,
            sampleRate: 48000,
            sampleSize: 16,
          },
          video: options.withVideo
            ? {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                frameRate: { ideal: 30, max: 30 },
              }
            : false,
        })
        this.coachCaptureMode = options.withVideo ? 'video' : 'audio'
        const analysisMimeType = this.pickRecordingMimeType()
        const mixedMimeType = this.pickMixedRecordingMimeType()
        this.mediaStream = stream
        this.analysisStream = new MediaStream(stream.getAudioTracks())
        this.recordedChunks = []
        this.mixedChunks = []
        const mixedStream = await this.buildMixedRecordingStream(stream, { withVideo: options.withVideo })
        this.mediaRecorder = analysisMimeType
          ? new MediaRecorder(this.analysisStream, { mimeType: analysisMimeType })
          : new MediaRecorder(this.analysisStream)
        this.mixRecorder = mixedMimeType
          ? new MediaRecorder(mixedStream, { mimeType: mixedMimeType })
          : new MediaRecorder(mixedStream)
        this.mediaRecorder.addEventListener('dataavailable', event => {
          if (event.data?.size) {
            this.recordedChunks.push(event.data)
          }
        })
        this.mixRecorder.addEventListener('dataavailable', event => {
          if (event.data?.size) {
            this.mixedChunks.push(event.data)
          }
        })
        const finalizeRecording = () => {
          this.finishCoachRecording().catch(error => {
            this.coachError = error.message || '录音分析失败'
          })
        }
        this.mixRecorder.addEventListener('stop', finalizeRecording, { once: true })
        this.videoCoachActive = Boolean(options.withVideo)
        this.coachPlaybackActive = Boolean(options.autoplay) && !options.withVideo
        if (options.countdown && options.countdown > 0) {
          await this.runCoachCountdown(options.countdown)
        }
        this.coachRecordingStartedAt = Date.now()
        this.isRecording = true
        this.mediaRecorder.start()
        this.mixRecorder.start()
        if (options.autoplay) {
          this.audio.currentTime = this.playbackStartTime()
          await this.audio.play().catch(error => {
            this.coachPlaybackActive = false
            this.videoCoachActive = false
            throw error
          })
        }
      } catch (error) {
        this.coachPlaybackActive = false
        this.videoCoachActive = false
        this.clearCoachCountdown()
        this.stopCoachStream()
        this.coachError = error.message || '无法访问麦克风或摄像头，请检查浏览器权限。'
      }
    },
    stopCoachRecording() {
      if ((!this.mediaRecorder || this.mediaRecorder.state === 'inactive') && (!this.mixRecorder || this.mixRecorder.state === 'inactive')) return
      if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') this.mediaRecorder.stop()
      if (this.mixRecorder && this.mixRecorder.state !== 'inactive') this.mixRecorder.stop()
      this.coachPlaybackActive = false
      this.isRecording = false
      this.coachRecordingDuration = Math.max(0, (Date.now() - this.coachRecordingStartedAt) / 1000)
      this.stopCoachStream()
    },
    async finishCoachRecording() {
      const captureMode = this.coachCaptureMode
      const recordingDuration = this.coachRecordingDuration
      const analysisBlob = new Blob(this.recordedChunks, {
        type: this.mediaRecorder?.mimeType || (captureMode === 'video' ? 'video/webm' : 'audio/webm'),
      })
      const mixedBlob = new Blob(this.mixedChunks, {
        type: this.mixRecorder?.mimeType || (captureMode === 'video' ? 'video/webm' : 'audio/webm'),
      })
      this.recordedChunks = []
      this.mixedChunks = []
      this.mediaRecorder = null
      this.mixRecorder = null
      this.stopCoachStream()

      if (!analysisBlob.size || !mixedBlob.size) {
        this.coachError = captureMode === 'video'
          ? '没有录到有效音画内容，请确认摄像头和 Scarlett 2i2 输入正常。'
          : '没有录到有效音频，请确认 Scarlett 2i2 或麦克风输入正常。'
        return
      }

      this.setCoachRecordingPreview(mixedBlob)
      this.pendingCoachTake = {
        analysisBlob,
        mixedBlob,
        captureMode,
        recordingDuration,
      }
      this.setPracticeSideTab('record')
    },
    async savePendingCoachTake() {
      if (!this.pendingCoachTake) return
      const pending = this.pendingCoachTake
      await this.submitCoachRecording(pending.analysisBlob, pending.mixedBlob, {
        captureMode: pending.captureMode,
        recordingDuration: pending.recordingDuration,
      })
    },
    async retryPendingCoachTake() {
      if (!this.pendingCoachTake) return
      const captureMode = this.pendingCoachTake.captureMode
      this.pendingCoachTake = null
      this.clearCoachRecordingPreview()
      this.coachError = ''
      if (captureMode === 'video') {
        await this.startVideoCoachPlayback()
        return
      }
      await this.startCoachPlayback()
    },
    cancelPendingCoachTake() {
      if (!this.pendingCoachTake) return
      this.pendingCoachTake = null
      this.coachError = ''
      this.coachRecordingDuration = 0
      this.clearCoachRecordingPreview()
    },
    async submitCoachRecording(blob, mixedBlob, options = {}) {
      this.coachAnalyzing = true
      this.coachError = ''

      try {
        const formData = new FormData()
        formData.append('song_id', this.selectedSong.id)
        formData.append('song_title', this.selectedSong.title)
        formData.append('version', this.selectedVersion)
        formData.append('segment_label', this.versionLeafLabel(this.selectedVersion))
        formData.append('playback_rate', String(this.playbackRate))
	        formData.append('recorded_duration', String(options.recordingDuration || this.coachRecordingDuration || 0))
	        formData.append('reference_start_seconds', String(this.playbackStartTime()))
	        formData.append('coach_model', this.coachModel)
        formData.append('capture_mode', options.captureMode || this.coachCaptureMode)
        formData.append('reference_asset_path', this.currentAudioFile)
        formData.append('media', blob, `practice-take.${this.recordingExtension(blob.type)}`)
        formData.append('mix_media', mixedBlob, `practice-mix.${this.recordingExtension(mixedBlob.type)}`)

        const response = await fetch('/api/coach/analyze-rhythm', {
          method: 'POST',
          body: formData,
        })

        const data = await response.json()
        if (!response.ok) {
          throw new Error(data.detail || '练习回放保存失败')
        }

        this.coachResult = data
        this.pendingCoachTake = null
        this.upsertCoachSession(data)
        this.lastSavedCoachSessionId = data.session_id || ''
        await this.loadCoachSessions()
        this.setPracticeSideTab('history')
      } catch (error) {
        this.coachError = error.message || '练习回放保存失败'
      } finally {
        this.coachAnalyzing = false
      }
    },
    resetCoachResult() {
      this.coachError = ''
      this.coachResult = null
      this.pendingCoachTake = null
      this.coachRecordingDuration = 0
      this.clearCoachRecordingPreview()
      this.stopCoachSegmentPlayback()
    },
    async loadCoachSessions() {
      try {
        const response = await fetch('/api/coach/sessions')
        if (!response.ok) throw new Error('练习记录加载失败')
        this.coachHistory = await response.json()
      } catch {
        this.coachHistory = []
      }
    },
    upsertCoachSession(session) {
      if (!session?.session_id) return
      const next = [session, ...this.coachHistory.filter(item => item.session_id !== session.session_id)]
      this.coachHistory = next
    },
    toggleCoachSessionSelection(sessionId) {
      if (this.selectedCoachSessionIds.includes(sessionId)) {
        this.selectedCoachSessionIds = this.selectedCoachSessionIds.filter(item => item !== sessionId)
        return
      }
      this.selectedCoachSessionIds = [...this.selectedCoachSessionIds, sessionId]
    },
    async deleteSelectedCoachSessions() {
      if (!this.selectedVisibleCoachSessionIds.length) return
      const idsToDelete = [...this.selectedVisibleCoachSessionIds]
      const confirmed = window.confirm(`确定删除当前歌曲下选中的 ${idsToDelete.length} 条练习记录吗？`)
      if (!confirmed) return
      const response = await fetch('/api/coach/sessions', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_ids: idsToDelete }),
      })
      const data = await response.json()
      if (!response.ok) {
        window.alert(data.detail || '删除失败')
        return
      }
      this.coachHistory = data.sessions || []
      this.selectedCoachSessionIds = this.selectedCoachSessionIds.filter(id => !idsToDelete.includes(id))
    },
    exportSelectedCoachSessions() {
      if (!this.selectedVisibleCoachSessionIds.length) return
      const url = `/api/coach/sessions/export?ids=${encodeURIComponent(this.selectedVisibleCoachSessionIds.join(','))}`
      window.open(url, '_blank', 'noopener')
    },
    loadCoachModel() {
      try {
        return window.localStorage.getItem(COACH_MODEL_STORAGE_KEY) || COACH_MODELS[0].value
      } catch {
        return COACH_MODELS[0].value
      }
    },
    persistCoachModel() {
      try {
        window.localStorage.setItem(COACH_MODEL_STORAGE_KEY, this.coachModel)
      } catch {}
    },
    handleCoachModelChange(event) {
      const model = event?.detail?.model
      if (!model) return
      this.coachModel = model
    },
    loadPracticeSideTab() {
      try {
        const saved = window.localStorage.getItem(PRACTICE_SIDE_TAB_STORAGE_KEY) || 'record'
        if (saved === 'coach' || saved === 'ai') return 'record'
        return saved
      } catch {
        return 'record'
      }
    },
    setPracticeSideTab(tab) {
      this.practiceSideTab = tab
      try {
        window.localStorage.setItem(PRACTICE_SIDE_TAB_STORAGE_KEY, tab)
      } catch {}
    },
    setCoachRecordingPreview(blob) {
      this.clearCoachRecordingPreview()
      this.coachRecordingUrl = URL.createObjectURL(blob)
      this.coachPlaybackAudio = this.coachCaptureMode === 'video' ? null : new Audio(this.coachRecordingUrl)
    },
    clearCoachRecordingPreview() {
      if (this.coachPlaybackAudio) {
        this.coachPlaybackAudio.pause()
        this.coachPlaybackAudio.src = ''
        this.coachPlaybackAudio = null
      }
      if (this.coachRecordingUrl) {
        URL.revokeObjectURL(this.coachRecordingUrl)
        this.coachRecordingUrl = ''
      }
    },
    stopCoachSegmentPlayback() {
      this.coachCompareToken += 1
      if (this.coachPlaybackStopTimer) {
        window.clearTimeout(this.coachPlaybackStopTimer)
        this.coachPlaybackStopTimer = null
      }
      if (this.coachPlaybackAudio) {
        this.coachPlaybackAudio.pause()
      }
      if (this.audio) {
        this.audio.pause()
      }
    },
    async playCoachSegment(segment) {
      if (!this.coachPlaybackAudio || !this.coachRecordingUrl) return
      const token = this.beginCoachPlayback()
      await this.playSegmentOnAudio(this.coachPlaybackAudio, segment, token)
    },
    async playReferenceSegment(segment) {
      if (!this.audio || !this.currentAudioFile) return
      const token = this.beginCoachPlayback()
      await this.playSegmentOnAudio(this.audio, segment, token)
    },
    async playABCompare(segment) {
      if (!this.coachPlaybackAudio || !this.coachRecordingUrl || !this.audio || !this.currentAudioFile) return
      const token = this.beginCoachPlayback()
      await this.playSegmentOnAudio(this.coachPlaybackAudio, segment, token)
      if (token !== this.coachCompareToken) return
      await this.waitCoachPlayback(220, token)
      if (token !== this.coachCompareToken) return
      await this.playSegmentOnAudio(this.audio, segment, token)
    },
    beginCoachPlayback() {
      this.stopCoachSegmentPlayback()
      return this.coachCompareToken
    },
    async playSegmentOnAudio(targetAudio, segment, token) {
      if (!targetAudio || token !== this.coachCompareToken) return
      const start = Math.max(0, Number(segment.start) || 0)
      const end = Math.max(start + 0.2, Number(segment.end) || start + 0.2)
      targetAudio.currentTime = start
      await targetAudio.play().catch(() => {})
      if (token !== this.coachCompareToken) return
      await this.waitCoachPlayback(Math.max(250, (end - start) * 1000), token)
      if (token !== this.coachCompareToken) return
      targetAudio.pause()
      targetAudio.currentTime = start
    },
    waitCoachPlayback(delay, token) {
      return new Promise(resolve => {
        this.coachPlaybackStopTimer = window.setTimeout(() => {
          if (token === this.coachCompareToken) {
            this.coachPlaybackStopTimer = null
          }
          resolve()
        }, delay)
      })
    },
    stopCoachStream() {
      if (this.currentInputSource) {
        try {
          this.currentInputSource.disconnect()
        } catch {}
        this.currentInputSource = null
      }
      if (this.analysisStream) {
        this.analysisStream.getTracks().forEach(track => track.stop())
        this.analysisStream = null
      }
      if (!this.mediaStream) return
      this.mediaStream.getTracks().forEach(track => track.stop())
      this.mediaStream = null
    },
    async runCoachCountdown(seconds) {
      this.clearCoachCountdown()
      this.coachCountdown = seconds
      await new Promise(resolve => {
        const tick = () => {
          if (this.coachCountdown <= 1) {
            this.coachCountdown = 0
            this.coachCountdownTimer = null
            resolve()
            return
          }
          this.coachCountdown -= 1
          this.coachCountdownTimer = window.setTimeout(tick, 1000)
        }
        this.coachCountdownTimer = window.setTimeout(tick, 1000)
      })
    },
    clearCoachCountdown() {
      if (this.coachCountdownTimer) {
        window.clearTimeout(this.coachCountdownTimer)
        this.coachCountdownTimer = null
      }
      this.coachCountdown = 0
    },
    async buildMixedRecordingStream(stream, options = {}) {
      if (!this.audioContext) {
        this.audioContext = new window.AudioContext()
      }
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume()
      }
      if (!this.mixDestination) {
        this.mixDestination = this.audioContext.createMediaStreamDestination()
      }
      if (!this.backingSourceNode) {
        this.backingSourceNode = this.audioContext.createMediaElementSource(this.audio)
        this.backingMonitorGain = this.audioContext.createGain()
        this.backingRecordGain = this.audioContext.createGain()
        this.backingMonitorGain.gain.value = this.backingVolume
        this.backingRecordGain.gain.value = this.backingVolume * 0.92
        this.backingSourceNode.connect(this.backingMonitorGain)
        this.backingMonitorGain.connect(this.audioContext.destination)
        this.backingSourceNode.connect(this.backingRecordGain)
        this.backingRecordGain.connect(this.mixDestination)
      }
      this.applyBackingVolume()
      if (this.currentInputSource) {
        try {
          this.currentInputSource.disconnect()
        } catch {}
      }
      this.currentInputSource = this.audioContext.createMediaStreamSource(new MediaStream(stream.getAudioTracks()))
      if (!this.inputRecordGain) {
        this.inputRecordGain = this.audioContext.createGain()
        this.inputRecordGain.gain.value = 1.0
      }
      this.currentInputSource.connect(this.inputRecordGain)
      this.inputRecordGain.connect(this.mixDestination)

      const tracks = [...this.mixDestination.stream.getAudioTracks()]
      if (options.withVideo) {
        tracks.push(...stream.getVideoTracks())
      }
      return new MediaStream(tracks)
    },
    pickRecordingMimeType() {
      const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4']
      return types.find(type => window.MediaRecorder?.isTypeSupported?.(type)) || ''
    },
    pickMixedRecordingMimeType() {
      if (this.coachCaptureMode === 'video') {
        const videoTypes = ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm', 'video/mp4']
        return videoTypes.find(type => window.MediaRecorder?.isTypeSupported?.(type)) || ''
      }
      const audioTypes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4']
      return audioTypes.find(type => window.MediaRecorder?.isTypeSupported?.(type)) || ''
    },
    recordingExtension(mimeType) {
      if (mimeType.includes('mp4')) return 'mp4'
      if (mimeType.includes('ogg')) return 'ogg'
      if (mimeType.includes('mpeg')) return 'mp3'
      return 'webm'
    },
    isVideoReplay(item) {
      return item?.mixed_kind === 'video'
        || item?.recording_kind === 'video'
        || item?.mixed_mime_type?.startsWith?.('video/')
        || item?.recording_mime_type?.startsWith?.('video/')
    },
    formatCoachSegmentTime(seconds) {
      if (!Number.isFinite(seconds)) return '0:00.0'
      const mins = Math.floor(seconds / 60)
      const secs = (seconds % 60).toFixed(1).padStart(4, '0')
      return `${mins}:${secs}`
    },
    formatCoachTimestamp(value) {
      if (!value) return '刚刚'
      const date = new Date(value)
      if (Number.isNaN(date.getTime())) return value
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
    },
    async openScore(type) {
      const file = this.selectedVersionFiles[type]
      if (!file) return
      this.gpError = ''
      this.scoreNotice = ''

      if (type === 'gp') {
        await this.openExternalSongAsset(file)
        return
      }

      this.scoreType = type
      this.scoreUrl = this.buildSongMediaUrl(file)
      this.showScoreModal = true

      if (type === 'pdf') {
        this.destroyGpApi()
      } else {
        await this.$nextTick()
        const rendered = await this.renderGP(this.scoreUrl)
        if (!rendered && this.selectedVersionFiles.pdf) {
          this.scoreType = 'pdf'
          this.scoreUrl = this.buildSongMediaUrl(this.selectedVersionFiles.pdf)
          this.scoreNotice = 'GP 暂时无法渲染，已自动切换到同版本 PDF 预览。'
          this.destroyGpApi()
        }
      }
    },
    async openExternalSongAsset(file) {
      if (!this.selectedSong?.id || !file) return
      try {
        const response = await fetch(
          `/api/songs/${this.selectedSong.id}/open-asset?path=${encodeURIComponent(file)}`,
          { method: 'POST' },
        )
        if (!response.ok) {
          const data = await response.json().catch(() => ({}))
          throw new Error(data.detail || '调用系统程序打开失败')
        }
      } catch (error) {
        window.alert(error.message || '调用系统程序打开失败')
      }
    },
    closeScoreModal() {
      this.showScoreModal = false
      this.scoreUrl = ''
      this.pdfDoc = null
      this.scoreNotice = ''
      this.destroyGpApi()
    },
    async renderGP(url) {
      this.gpLoading = true
      this.gpError = ''
      this.destroyGpApi()

      try {
        if (this.isFilePreview()) {
          throw new Error('静态预览模式无法直接渲染 GP 谱，请点击打开原始 GP 文件；本地服务模式会使用 alphaTab 渲染。')
        }
        const alphaTab = await this.ensureAlphaTab()
        const container = this.$refs.gpContainer
        if (!container) {
          throw new Error('GP 容器未找到')
        }

        container.innerHTML = ''
        this.gpApi = new alphaTab.AlphaTabApi(container, {
          file: url,
        })
        return true
      } catch (error) {
        this.gpError = `GP 谱加载失败：${error.message}`
        return false
      } finally {
        this.gpLoading = false
      }
    },
    async ensureAlphaTab() {
      if (window.alphaTab?.AlphaTabApi) {
        return window.alphaTab
      }

      await new Promise((resolve, reject) => {
        const existing = document.querySelector('script[data-alphatab="true"]')
        if (existing) {
          existing.addEventListener('load', () => resolve(), { once: true })
          existing.addEventListener('error', () => reject(new Error('alphaTab 脚本加载失败')), { once: true })
          return
        }

        const script = document.createElement('script')
        script.src = 'https://cdn.jsdelivr.net/npm/@coderline/alphatab@latest/dist/alphaTab.js'
        script.dataset.alphatab = 'true'
        script.onload = () => resolve()
        script.onerror = () => reject(new Error('alphaTab 脚本加载失败'))
        document.head.appendChild(script)
      })

      if (!window.alphaTab?.AlphaTabApi) {
        throw new Error('alphaTab 未正确初始化')
      }

      return window.alphaTab
    },
    destroyGpApi() {
      if (this.gpApi?.destroy) {
        this.gpApi.destroy()
      }
      this.gpApi = null
      this.gpLoading = false
      this.gpError = ''
    },
  },
}
</script>

<style scoped>
.songs-view {
  min-height: 680px;
}

.songs-layout {
  display: grid;
  grid-template-columns: 236px minmax(0, 1fr);
  gap: 10px;
}

.song-list,
.song-detail {
  background: #16213e;
  border-radius: 15px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  padding: 12px;
}

.song-list {
  position: sticky;
  top: 12px;
  max-height: calc(100vh - 40px);
  overflow: auto;
}

.list-header,
.detail-header,
.score-header,
.player-header,
.section-heading {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.detail-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.player-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.player-header-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.player-header-copy strong {
  color: #f8fafc;
  font-size: 15px;
  line-height: 1.35;
}

.player-header-eyebrow {
  color: #94a3b8;
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.playback-mode-group {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px;
  border-radius: 999px;
  background: rgba(8, 14, 28, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.playback-mode-option {
  position: relative;
  display: inline-flex;
  align-items: center;
  cursor: pointer;
}

.playback-mode-option input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.playback-mode-option span {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  color: #94a3b8;
  font-size: 11.5px;
  line-height: 1;
  transition: background-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
}

.playback-mode-option input:checked + span {
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.22), rgba(251, 146, 60, 0.1));
  color: #fff7ed;
  transform: translateY(-1px);
}

.player-mode-hint {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 7px;
  margin: 0 0 4px;
  color: #94a3b8;
  font-size: 11.5px;
}

.sync-offset-picker {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #cbd5e1;
  font-size: 12px;
}

.sync-offset-picker span {
  color: #94a3b8;
  white-space: nowrap;
}

.sync-offset-picker select {
  border-radius: 999px;
  border: 1px solid rgba(249, 115, 22, 0.35);
  background: #0f1730;
  color: #f8fafc;
  padding: 7px 10px;
  font-size: 12px;
}

.list-header {
  margin-bottom: 10px;
}

.list-header h2,
.detail-header h3,
.versions-section h4,
.score-section h4 {
  color: #f3f4f6;
}

.list-header p,
.detail-header p,
.empty-copy,
.song-card p {
  color: #94a3b8;
}

.search-box {
  display: grid;
  gap: 7px;
  margin-bottom: 10px;
  color: #cbd5e1;
  font-size: 12.5px;
}

.search-box input {
  border-radius: 11px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: #0f1730;
  color: #f8fafc;
  padding: 9px 11px;
}

.recent-practice-block {
  display: grid;
  gap: 8px;
  margin-bottom: 10px;
}

.recent-practice-list {
  display: grid;
  gap: 8px;
}

.recent-practice-card {
  width: 100%;
  text-align: left;
  border: 1px solid rgba(90, 174, 255, 0.22);
  border-radius: 11px;
  background: rgba(8, 14, 28, 0.78);
  color: #e5e7eb;
  padding: 9px 10px 8px;
  cursor: pointer;
}

.recent-practice-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.recent-practice-card strong {
  display: block;
  font-size: 12.5px;
  line-height: 1.35;
}

.recent-practice-jump {
  flex-shrink: 0;
  border-radius: 999px;
  padding: 2px 7px;
  background: rgba(249, 115, 22, 0.14);
  color: #fb923c;
  font-size: 10px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.recent-practice-card p {
  margin-top: 2px;
  color: #cbd5e1;
  font-size: 11.5px;
}

.recent-practice-meta {
  margin-top: 6px;
}

.song-card,
.version-item,
.marker-item,
.group-item {
  width: 100%;
  text-align: left;
  border: 1px solid transparent;
  border-radius: 10px;
  background: #0f1730;
  color: #e5e7eb;
  padding: 8px 9px;
  margin-bottom: 6px;
  cursor: pointer;
}

.song-card strong,
.group-item strong,
.version-item span {
  font-size: 12.5px;
  line-height: 1.35;
}

.song-card p,
.group-item small,
.version-item small {
  font-size: 10.5px;
  line-height: 1.35;
}

.song-card.active,
.version-item.active,
.group-item.active {
  border-color: rgba(249, 115, 22, 0.7);
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.18), rgba(255, 255, 255, 0.04));
}

.song-card span,
.version-item small,
.group-item small,
.path-pill {
  color: #f97316;
}

.danger-btn {
  border: 1px solid rgba(248, 113, 113, 0.58);
  border-radius: 999px;
  background: rgba(127, 29, 29, 0.28);
  color: #fecaca;
  padding: 8px 14px;
  cursor: pointer;
  white-space: nowrap;
}

.danger-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.path-pill {
  display: inline-flex;
  border-radius: 999px;
  padding: 5px 10px;
  background: #0f1730;
  font-size: 12px;
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.versions-section,
.player-section,
.score-section,
.coach-section {
  margin-top: 14px;
  border-radius: 13px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(15, 23, 48, 0.56);
  padding: 9px;
}

.support-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.92fr) minmax(0, 1.08fr);
  gap: 9px;
}

.practice-shell {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(300px, 0.74fr);
  gap: 10px;
  align-items: start;
}

.practice-main,
.practice-side {
  min-width: 0;
}

.practice-main {
  display: grid;
  gap: 8px;
}

.practice-side {
  position: sticky;
  top: 16px;
  display: grid;
  gap: 8px;
}

.practice-side-tabs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
  position: sticky;
  top: 0;
  z-index: 2;
  padding: 7px;
  border-radius: 13px;
  background: rgba(8, 14, 28, 0.94);
  border: 1px solid rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(10px);
}

.practice-tab-btn {
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(15, 23, 48, 0.9);
  color: #cbd5e1;
  border-radius: 11px;
  padding: 8px 9px;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
}

.practice-tab-btn.active {
  border-color: rgba(249, 115, 22, 0.55);
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.18), rgba(255, 255, 255, 0.04));
  color: #fff7ed;
}

.versions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(114px, 1fr));
  gap: 5px;
  margin-top: 5px;
}

.group-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(116px, 1fr));
  gap: 5px;
  margin-top: 5px;
}

.group-item strong,
.version-item span {
  display: block;
}

.segments-section {
  margin-top: 14px;
}

.section-copy {
  color: #94a3b8;
  font-size: 11.5px;
}

.detail-header h3 {
  font-size: 24px;
  line-height: 1.1;
}

.detail-header p {
  margin-top: 3px;
  font-size: 13px;
}

.transport-bar {
  display: grid;
  gap: 5px;
  padding: 7px 9px;
  border-radius: 12px;
  background: rgba(15, 23, 48, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.seek-slider,
.modal-seek {
  width: 100%;
  accent-color: #f97316;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #f97316, #fb7185);
}

.time-row {
  display: flex;
  justify-content: space-between;
  color: #94a3b8;
  font-size: 11.5px;
  margin-top: 0;
}

.transport-meta {
  display: grid;
  grid-template-columns: minmax(104px, 0.36fr) minmax(0, 1fr);
  align-items: center;
  gap: 7px;
}

.control-row {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 0;
}

.volume-row {
  align-items: center;
}

.volume-slider {
  flex: 1 1 140px;
  min-width: 120px;
  accent-color: #f97316;
}

.volume-row strong {
  min-width: 44px;
  text-align: right;
  color: #fff7ed;
  font-size: 11px;
}

.control-row button,
.score-actions button,
.ghost-btn,
.play-btn,
.modal-audio-controls button {
  border: 1px solid rgba(249, 115, 22, 0.4);
  background: transparent;
  color: #f97316;
  border-radius: 999px;
  padding: 5px 9px;
  font-size: 11px;
  cursor: pointer;
}

.play-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 34px;
  padding-inline: 11px;
  font-weight: 600;
}

.play-btn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.1rem;
  font-size: 0.9rem;
  line-height: 1;
}

.play-btn.record-mode {
  border-color: rgba(248, 113, 113, 0.52);
  color: #fca5a5;
  background: rgba(127, 29, 29, 0.16);
}

.play-btn.record-mode .play-btn-icon {
  color: #ef4444;
}

.play-btn.save-btn {
  border-color: rgba(34, 197, 94, 0.38);
  color: #dcfce7;
  background: rgba(20, 83, 45, 0.38);
}

.play-btn.save-btn .play-btn-icon {
  color: #86efac;
}

.control-row button.active {
  background: #f97316;
  color: #fff7ed;
}

.audio-options {
  display: grid;
  gap: 7px;
  margin: 8px 0 4px;
}

.audio-options-label {
  color: #94a3b8;
  font-size: 11px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.audio-options-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.audio-option-btn {
  border: 1px solid rgba(148, 163, 184, 0.28);
  background: rgba(15, 23, 48, 0.7);
  color: #cbd5e1;
  border-radius: 999px;
  padding: 5px 9px;
  font-size: 11.5px;
  cursor: pointer;
}

.audio-option-btn.active {
  border-color: rgba(249, 115, 22, 0.55);
  background: rgba(249, 115, 22, 0.16);
  color: #fb923c;
}

.loop-row {
  justify-content: flex-end;
}

.loop-snippet-panel {
  display: grid;
  gap: 7px;
  margin-top: 2px;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.loop-snippet-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.loop-snippet-head strong {
  color: #f8fafc;
  font-size: 12.5px;
}

.loop-snippet-head p {
  margin-top: 2px;
  color: #94a3b8;
  font-size: 11.5px;
}

.loop-snippet-current {
  color: #cbd5e1;
}

.loop-snippet-form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 7px;
}

.loop-snippet-form input {
  width: 100%;
  border-radius: 11px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(15, 23, 48, 0.82);
  color: #f8fafc;
  padding: 8px 10px;
  font-size: 12.5px;
}

.loop-snippet-list {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  max-height: 220px;
  overflow: auto;
  padding-right: 4px;
}

.loop-snippet-card {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: space-between;
  gap: 8px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(8, 14, 28, 0.76);
  padding: 8px 10px;
  min-width: 0;
}

.loop-snippet-meta {
  min-width: 0;
}

.loop-snippet-link {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  border: 0;
  background: transparent;
  padding: 0;
  color: #f8fafc;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.3;
  cursor: pointer;
  text-align: left;
}

.loop-snippet-link:hover {
  color: #f97316;
}

.loop-snippet-link:focus-visible {
  outline: 2px solid rgba(249, 115, 22, 0.55);
  outline-offset: 2px;
  border-radius: 6px;
}

.loop-snippet-meta p {
  margin-top: 2px;
  color: #94a3b8;
  font-size: 12px;
}

.loop-snippet-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: flex-end;
  flex-shrink: 0;
}

.danger-ghost {
  border-color: rgba(248, 113, 113, 0.35);
  color: #fca5a5;
}

.cancel-btn {
  min-width: 88px;
}

.loop-snippet-sibling-groups {
  display: grid;
  gap: 8px;
}

.loop-snippet-sibling-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.score-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin: 4px 0 2px;
}

.score-actions a {
  display: inline-flex;
  align-items: center;
  border: 1px solid rgba(249, 115, 22, 0.4);
  color: #f97316;
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 11.5px;
  text-decoration: none;
}

.score-header {
  align-items: flex-start;
}

.score-header > div {
  min-width: 0;
}

.score-header h4 {
  line-height: 1.2;
}

.score-header p {
  margin-top: 2px;
  font-size: 12px;
  line-height: 1.45;
}

.media-hints {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.media-hints span {
  border-radius: 999px;
  background: rgba(15, 23, 48, 0.9);
  color: #cbd5e1;
  padding: 5px 9px;
  font-size: 11px;
}

.compact-hints {
  margin-bottom: 0;
}

.markers-list {
  display: grid;
  gap: 10px;
  max-height: 220px;
  overflow: auto;
  padding-right: 4px;
}

.related-video-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 7px;
}

.related-video-card {
  display: grid;
  grid-template-columns: 76px minmax(0, 1fr) auto;
  align-items: center;
  gap: 7px;
  padding: 8px;
  border-radius: 11px;
  background: #0f1730;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.related-video-thumb {
  position: relative;
  display: grid;
  place-items: center;
  min-height: 66px;
  border-radius: 9px;
  overflow: hidden;
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.32), rgba(15, 23, 48, 0.92));
}

.related-video-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.related-video-thumb span {
  color: rgba(255, 247, 237, 0.92);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.06em;
}

.related-video-main {
  min-width: 0;
}

.related-video-main strong {
  display: block;
  color: #f8fafc;
  font-size: 11.5px;
  line-height: 1.4;
}

.related-video-main p {
  margin-top: 3px;
  color: #94a3b8;
  font-size: 10.5px;
  line-height: 1.4;
}

.related-video-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.coach-copy {
  margin-top: 2px;
  color: #94a3b8;
  font-size: 11.5px;
  line-height: 1.5;
  max-width: 40ch;
}

.coach-copy-success {
  color: #9ae6b4;
}

.coach-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 8px;
  background: rgba(249, 115, 22, 0.14);
  color: #f97316;
  font-size: 10.5px;
}

.coach-header-side {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.coach-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 8px;
}

.pending-actions {
  justify-content: flex-end;
}

.retry-btn {
  border-color: rgba(148, 163, 184, 0.24);
  color: #cbd5e1;
}

.coach-error {
  margin-top: 12px;
  border-radius: 14px;
  padding: 12px 14px;
  background: rgba(127, 29, 29, 0.28);
  border: 1px solid rgba(248, 113, 113, 0.38);
  color: #fecaca;
}

.coach-result {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 8px;
}

.coach-focus-card {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  padding: 10px 11px;
  border-radius: 13px;
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.16), rgba(8, 14, 28, 0.88));
  border: 1px solid rgba(249, 115, 22, 0.18);
}

.coach-focus-block {
  min-width: 0;
}

.coach-focus-label {
  display: inline-block;
  margin-bottom: 5px;
  color: #fdba74;
  font-size: 10.5px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.coach-focus-block strong,
.coach-focus-block p {
  color: #fff7ed;
  font-size: 12.5px;
  line-height: 1.55;
}

.pending-coach-result {
  grid-template-columns: minmax(0, 1fr);
}

.pending-coach-head {
  display: grid;
  gap: 8px;
}

.coach-history {
  display: grid;
  gap: 8px;
  margin-top: 8px;
}

.coach-history-list {
  display: grid;
  gap: 5px;
  max-height: 520px;
  overflow: auto;
  padding-right: 4px;
}

.coach-history-card {
  position: relative;
  border-radius: 11px;
  background: #0f1730;
  border: 1px solid rgba(255, 255, 255, 0.06);
  padding: 8px 9px 8px 14px;
}

.coach-history-card.fresh {
  border-color: rgba(90, 174, 255, 0.42);
  box-shadow: 0 0 0 1px rgba(90, 174, 255, 0.18);
}

.coach-history-rail {
  position: absolute;
  left: 8px;
  top: 10px;
  bottom: 10px;
  width: 2px;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(249, 115, 22, 0.9), rgba(59, 130, 246, 0.3));
}

.coach-history-select {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #cbd5e1;
  font-size: 12px;
}

.coach-history-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-top: 5px;
}

.coach-history-head strong {
  display: block;
  color: #f8fafc;
  font-size: 12px;
  line-height: 1.4;
}

.coach-history-head p {
  margin-top: 2px;
  color: #94a3b8;
  font-size: 10.5px;
  line-height: 1.45;
}

.coach-history-score {
  white-space: nowrap;
  color: #f97316;
  font-size: 10.5px;
}

.coach-history-media {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
  margin-top: 8px;
}

.coach-media-player {
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  padding: 8px 9px;
}

.coach-media-player span {
  display: block;
  color: #94a3b8;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 8px;
}

.coach-media-player audio {
  width: 100%;
}

.coach-video-player {
  width: 100%;
  max-height: 360px;
  border-radius: 10px;
  background: #020617;
}

.coach-history-feedback {
  margin-top: 8px;
  color: #e5e7eb;
  line-height: 1.5;
  font-size: 13px;
}

.coach-history-feedback p {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

@media (max-width: 1180px) {
  .practice-shell {
    grid-template-columns: 1fr;
  }

  .practice-side {
    position: static;
  }

  .support-grid {
    grid-template-columns: 1fr;
  }

  .transport-meta {
    grid-template-columns: 1fr;
  }

  .loop-row {
    justify-content: flex-start;
  }

  .loop-snippet-form {
    grid-template-columns: 1fr;
  }

  .loop-snippet-card {
    align-items: flex-start;
    flex-direction: column;
  }

  .loop-snippet-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .coach-focus-card {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1280px) {
  .loop-snippet-list {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 860px) {
  .loop-snippet-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.coach-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.coach-metric,
.coach-block {
  border-radius: 14px;
  background: #0f1730;
  border: 1px solid rgba(255, 255, 255, 0.06);
  padding: 12px;
}

.coach-metric-primary,
.coach-block-wide {
  grid-column: 1 / -1;
}

.coach-block-compact {
  align-self: start;
}

.coach-metric span,
.coach-block h5 {
  color: #94a3b8;
  font-size: 11px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.coach-metric strong {
  display: block;
  margin-top: 4px;
  color: #f8fafc;
  font-size: 16px;
}

.coach-metric-tag {
  display: inline-flex;
  margin-top: 8px;
  color: #f97316;
  font-size: 11px;
  font-style: normal;
}

.learning-links {
  display: grid;
  gap: 8px;
}

.learning-link-card {
  display: grid;
  gap: 5px;
  padding: 10px 11px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.learning-link-actions {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  margin-top: 2px;
}

.compact-hints {
  margin-bottom: 0;
}

.learning-path {
  display: grid;
  gap: 8px;
}

.learning-path-step {
  display: grid;
  gap: 5px;
  padding: 10px 11px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.learning-path-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.learning-path-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.learning-path-index,
.learning-path-minutes {
  color: #94a3b8;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.learning-path-status {
  color: #f97316;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.learning-path-step strong {
  color: #f8fafc;
  font-size: 13px;
  line-height: 1.45;
}

.learning-path-step p {
  color: #cbd5e1;
  font-size: 12px;
  line-height: 1.55;
}

.learning-path-controls {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.learning-link-card strong {
  color: #f8fafc;
  font-size: 12px;
  line-height: 1.45;
}

.learning-link-card p {
  color: #cbd5e1;
  font-size: 11px;
  line-height: 1.45;
}

.learning-link-card span {
  color: #f97316;
  font-size: 11px;
}

.coach-block h5 {
  margin-bottom: 8px;
}

.coach-block ul {
  padding-left: 18px;
  color: #e5e7eb;
  display: grid;
  gap: 6px;
  line-height: 1.5;
  font-size: 13px;
}

.coach-plan-list {
  margin-top: 10px;
}

.interactive-plan-list {
  padding-left: 0;
  list-style: none;
  display: grid;
  gap: 8px;
}

.plan-check-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  color: #e5e7eb;
  line-height: 1.45;
  font-size: 13px;
}

.plan-check-item input {
  margin-top: 2px;
}

.coach-block p {
  color: #e5e7eb;
  line-height: 1.55;
  font-size: 13px;
}

.compact-empty {
  min-height: 96px;
}

.compact-empty {
  min-height: 96px;
}

.coach-plan-block > p + p {
  color: #cbd5e1;
}

.coach-segments {
  display: grid;
  gap: 12px;
}

.coach-segment-card {
  border-radius: 14px;
  border: 1px solid rgba(249, 115, 22, 0.16);
  background: rgba(15, 23, 48, 0.72);
  padding: 12px;
}

.coach-segment-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.coach-segment-head strong {
  color: #f8fafc;
}

.coach-segment-head span {
  color: #94a3b8;
  font-size: 12px;
  white-space: nowrap;
}

.coach-segment-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
}

.coach-segment-note {
  color: #fbbf24;
}

.marker-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.state-box {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 140px;
  border-radius: 14px;
  background: #0f1730;
  color: #94a3b8;
  text-align: center;
}

.score-modal {
  position: fixed;
  inset: 0;
  background: rgba(4, 8, 19, 0.82);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 1000;
}

.score-modal-content {
  width: min(1100px, 100%);
  max-height: 92vh;
  overflow: auto;
  background: #111827;
  border-radius: 20px;
  padding: 20px;
}

.related-video-modal-content {
  width: min(860px, 100%);
}

.score-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  color: #e5e7eb;
}

.score-modal-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ghost-link,
.inline-score-link {
  border: 1px solid rgba(249, 115, 22, 0.4);
  color: #f97316;
  border-radius: 999px;
  padding: 8px 14px;
  text-decoration: none;
  font-size: 14px;
}

.inline-score-link {
  display: inline-flex;
  margin-left: 10px;
}

.modal-audio-controls {
  display: grid;
  gap: 10px;
  color: #e5e7eb;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(8, 13, 28, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.modal-toolbar,
.modal-primary-controls,
.modal-utility-controls,
.modal-loop-cluster {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.modal-toolbar {
  justify-content: space-between;
}

.modal-primary-controls {
  gap: 12px;
}

.modal-utility-controls {
  justify-content: flex-end;
}

.modal-play-btn {
  min-width: 74px;
  font-weight: 700;
}

.modal-status-chip {
  display: grid;
  gap: 2px;
  min-width: 92px;
  padding: 7px 12px;
  border-radius: 12px;
  background: rgba(15, 23, 48, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.modal-status-chip span,
.speed-label {
  color: #94a3b8;
  font-size: 11px;
  line-height: 1;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.modal-status-chip strong {
  color: #f8fafc;
  font-size: 14px;
  font-weight: 600;
}

.speed-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 4px;
  border-radius: 999px;
  background: rgba(15, 23, 48, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.modal-speed-cluster {
  display: flex;
  align-items: center;
  gap: 8px;
}

.modal-loop-cluster button,
.modal-speed-cluster button {
  padding: 7px 12px;
  font-size: 13px;
}

.modal-speed-cluster button.active {
  background: #f97316;
  color: #fff7ed;
  border-color: #f97316;
}

.control-row button:disabled,
.score-actions button:disabled,
.ghost-btn:disabled,
.play-btn:disabled,
.modal-audio-controls button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.score-viewer {
  margin: 20px 0;
  border-radius: 18px;
  background: #0b1224;
  min-height: 320px;
  padding: 20px;
}

.related-video-frame {
  margin-top: 18px;
  border-radius: 16px;
  overflow: hidden;
  background: #050816;
}

.related-video-frame video {
  width: 100%;
  max-height: min(68vh, 640px);
  display: block;
  background: #000;
  object-fit: contain;
}

.gp-shell {
  min-height: 320px;
}

.gp-container {
  min-height: 320px;
  overflow: auto;
  background: #fff;
  border-radius: 12px;
  padding: 12px;
}

.pdf-container {
  display: flex;
  justify-content: center;
  min-height: 72vh;
}

.pdf-container iframe {
  width: 100%;
  min-height: 72vh;
  border: 0;
  border-radius: 12px;
  background: #fff;
}

@media (max-width: 960px) {
  .songs-layout {
    grid-template-columns: 1fr;
  }

  .song-list {
    position: static;
    max-height: none;
  }

  .coach-result {
    grid-template-columns: 1fr;
  }

  .modal-toolbar {
    justify-content: flex-start;
  }

  .modal-utility-controls {
    justify-content: flex-start;
  }
}
</style>
