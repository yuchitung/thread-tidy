import React, { useState, useEffect, useMemo } from 'react';

function App() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTags, setSelectedTags] = useState(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [showKeywords, setShowKeywords] = useState(false);

  useEffect(() => {
    loadPosts();
  }, []);

  const loadPosts = async () => {
    try {
      const response = await fetch('./posts.json');
      const data = await response.json();
      setPosts(data);
    } catch (error) {
      console.error('Failed to load posts:', error);
    } finally {
      setLoading(false);
    }
  };

  // Extract all tags (include keywords based on settings)
  const allTags = useMemo(() => {
    const tagSet = new Set();
    posts.forEach(post => {
      // Always include categories
      post.categories?.forEach(cat => tagSet.add(`cat:${cat}`));
      // Include keywords based on settings
      if (showKeywords) {
        post.keywords?.forEach(keyword => tagSet.add(`kw:${keyword}`));
      }
    });
    return Array.from(tagSet).sort();
  }, [posts, showKeywords]);

  // Filter posts
  const filteredPosts = useMemo(() => {
    return posts.filter(post => {
      // Tag filtering
      if (selectedTags.size > 0) {
        const hasSelectedTag = Array.from(selectedTags).some(selectedTag => {
          if (selectedTag.startsWith('cat:')) {
            const category = selectedTag.substring(4);
            return post.categories?.includes(category);
          } else if (selectedTag.startsWith('kw:')) {
            const keyword = selectedTag.substring(3);
            return post.keywords?.includes(keyword);
          }
          return false;
        });
        if (!hasSelectedTag) return false;
      }

      // Search filtering
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        return post.content.toLowerCase().includes(query) ||
               post.author.username.toLowerCase().includes(query) ||
               post.author.display_name.toLowerCase().includes(query);
      }

      return true;
    });
  }, [posts, selectedTags, searchQuery]);

  const toggleTag = (tag) => {
    const newSelectedTags = new Set(selectedTags);
    if (newSelectedTags.has(tag)) {
      newSelectedTags.delete(tag);
    } else {
      newSelectedTags.add(tag);
    }
    setSelectedTags(newSelectedTags);
  };

  const clearFilters = () => {
    setSelectedTags(new Set());
    setSearchQuery('');
  };

  // Clear selected keyword tags when keywords are hidden
  useEffect(() => {
    if (!showKeywords) {
      const newSelectedTags = new Set();
      selectedTags.forEach(tag => {
        if (tag.startsWith('cat:')) {
          newSelectedTags.add(tag);
        }
      });
      setSelectedTags(newSelectedTags);
    }
  }, [showKeywords]);

  const formatDate = (dateString) => {
    if (!dateString) return '';
    try {
      return new Date(dateString).toLocaleDateString('zh-TW', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return '';
    }
  };

  const MediaDisplay = ({ media, postUrl }) => {
    if (!media || media.length === 0) return null;

    return (
      <div className="grid grid-cols-[repeat(auto-fit,minmax(150px,1fr))] gap-3 my-4">
        {media.map((item, index) => {
          const isInstagramMedia = item.url.includes('instagram') || item.url.includes('fbcdn.net');
          
          if (isInstagramMedia) {
            // Instagram image placeholder
            return (
              <div key={index} className="flex flex-col items-center justify-center bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-5 min-h-[120px] text-center">
                <div className="text-2xl mb-2">📷</div>
                <div className="text-gray-600 text-sm md:text-base mb-2">圖片</div>
                <a href={postUrl} target="_blank" rel="noopener noreferrer" className="text-blue-500 no-underline text-sm py-1 px-2 rounded transition-colors duration-200 hover:bg-blue-50">
                  查看原貼文
                </a>
              </div>
            );
          } else {
            // External images (like YouTube) try to display directly
            return (
              <div key={index} className="relative">
                <img 
                  src={item.url} 
                  alt="Post media"
                  className="w-full h-auto rounded-lg max-h-[200px] object-cover"
                  onError={(e) => {
                    // Replace with placeholder if loading fails
                    e.target.style.display = 'none';
                    e.target.nextElementSibling.style.display = 'flex';
                  }}
                />
                <div className="flex flex-col items-center justify-center bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-5 min-h-[120px] text-center" style={{display: 'none'}}>
                  <div className="text-2xl mb-2">🖼️</div>
                  <div className="text-gray-600 text-sm md:text-base mb-2">圖片</div>
                  <a href={postUrl} target="_blank" rel="noopener noreferrer" className="text-blue-500 no-underline text-sm py-1 px-2 rounded transition-colors duration-200 hover:bg-blue-50">
                    查看原貼文
                  </a>
                </div>
              </div>
            );
          }
        })}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto p-5">
        <div className="text-center py-10 text-xl text-gray-600">載入中...</div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto p-5">
      <header className="text-center mb-8 p-5 bg-white rounded-xl shadow-md">
        <h1 className="text-3xl md:text-4xl font-bold mb-2 text-gray-800">🧵 ThreadTidy</h1>
        <p className="text-gray-600 text-sm md:text-base">我的 Threads 收藏整理</p>
      </header>

      <div className="mb-5">
        {/* Search box */}
        <div className="mb-5">
          <input
            type="text"
            placeholder="搜尋貼文內容、作者..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full py-3 px-4 border-2 border-gray-300 rounded-3xl text-sm md:text-base bg-white transition-colors duration-200 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Tag filtering */}
        {allTags.length > 0 && (
          <div className="bg-white p-4 rounded-xl shadow-md">
            <div className="flex justify-between items-center mb-3 font-medium text-gray-800">
              <span>標籤篩選:</span>
              <div className="flex items-center gap-3">
                <button 
                  onClick={() => setShowKeywords(!showKeywords)}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-sm md:text-base cursor-pointer transition-all duration-200 ${
                    showKeywords 
                      ? 'bg-blue-50 text-blue-600 border border-blue-200' 
                      : 'bg-gray-50 text-gray-600 border border-gray-300 hover:bg-gray-100 hover:border-gray-400'
                  }`}
                >
                  {showKeywords ? '🏷️ 隱藏關鍵字' : '🏷️ 顯示關鍵字'}
                </button>
                {selectedTags.size > 0 && (
                  <button onClick={clearFilters} className="bg-blue-50 text-blue-600 border-0 px-3 py-1 rounded-2xl text-sm md:text-base cursor-pointer transition-colors duration-200 hover:bg-blue-100">
                    清除篩選
                  </button>
                )}
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {allTags.map(tag => {
                const isCategory = tag.startsWith('cat:');
                const isKeyword = tag.startsWith('kw:');
                const displayText = isCategory ? tag.substring(4) : tag.substring(3);
                const chipClass = isCategory 
                  ? 'px-4 py-1.5 rounded-2xl text-sm md:text-base cursor-pointer transition-all duration-200 bg-green-50 text-green-700 border border-green-200 hover:bg-green-100'
                  : 'px-4 py-1.5 rounded-2xl text-sm md:text-base cursor-pointer transition-all duration-200 bg-orange-50 text-orange-600 border border-orange-200 hover:bg-orange-100';
                
                return (
                  <button
                    key={tag}
                    onClick={() => toggleTag(tag)}
                    className={`${chipClass} ${selectedTags.has(tag) 
                      ? (isCategory ? 'bg-green-500 text-white border-green-500' : 'bg-orange-500 text-white border-orange-500') 
                      : ''
                    }`}
                  >
                    {isCategory && '📂 '}{isKeyword && '🏷️ '}{displayText}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Statistics */}
      <div className="mb-5 py-3 px-4 bg-white rounded-lg text-sm md:text-base text-gray-600 shadow-sm">
        顯示 {filteredPosts.length} / {posts.length} 篇貼文
        {selectedTags.size > 0 && (
          <span className="text-blue-500">
            · 已篩選: {Array.from(selectedTags).map(tag => {
              return tag.startsWith('cat:') ? tag.substring(4) : tag.substring(3);
            }).join(', ')}
          </span>
        )}
      </div>

      {/* Posts list */}
      <div className="flex flex-col gap-4">
        {filteredPosts.length === 0 ? (
          <div className="text-center py-10 text-gray-600 bg-white rounded-xl shadow-md">
            {selectedTags.size > 0 || searchQuery ? '沒有符合條件的貼文' : '沒有貼文'}
          </div>
        ) : (
          filteredPosts.map(post => (
            <article key={post.post_id} className="bg-white rounded-xl p-5 shadow-md transition-shadow duration-200 hover:shadow-lg">
              <div className="flex justify-between items-start mb-3">
                <div className="flex flex-col">
                  <span className="font-semibold text-gray-800 text-base">{post.author.display_name}</span>
                  <span className="text-gray-600 text-sm md:text-base">@{post.author.username}</span>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <span className="text-gray-600 text-sm">{formatDate(post.timestamp)}</span>
                  <a 
                    href={post.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-500 no-underline text-sm md:text-base py-0.5 px-2 rounded transition-colors duration-200 hover:bg-blue-50"
                  >
                    查看原文
                  </a>
                </div>
              </div>

              <div className="mb-3 whitespace-pre-wrap leading-relaxed">
                {post.content}
              </div>

              <MediaDisplay media={post.media} postUrl={post.url} />

              {/* Tags display */}
              {(post.categories?.length > 0 || post.keywords?.length > 0) && (
                <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-gray-200">
                  {post.categories?.map(cat => (
                    <span key={cat} className="py-1 px-2.5 rounded-xl text-sm font-medium bg-green-50 text-green-700">{cat}</span>
                  ))}
                  {post.keywords?.map(keyword => (
                    <span key={keyword} className="py-1 px-2.5 rounded-xl text-sm font-medium bg-orange-50 text-orange-600">{keyword}</span>
                  ))}
                </div>
              )}
            </article>
          ))
        )}
      </div>
    </div>
  );
}

export default App;