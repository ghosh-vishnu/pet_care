import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { sendChatMessage, getChatMessages, uploadImage, uploadDocument } from '../services/api'
import { getPetId, getUserId } from '../config'
import { checkPetProfileStatus } from '../services/api'
import './Chat.css'

function Chat() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)
  const imageInputRef = useRef(null)

  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [petProfile, setPetProfile] = useState(null)

  useEffect(() => {
    loadMessages()
    loadProfile()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const loadProfile = async () => {
    try {
      const userId = getUserId()
      const petId = getPetId()
      const response = await checkPetProfileStatus(userId, petId)
      if (response.status === 'EXISTS' && response.profile_data) {
        setPetProfile(response.profile_data)
      }
    } catch (err) {
      console.error('Failed to load profile:', err)
    }
  }

  const loadMessages = async () => {
    try {
      const userId = getUserId()
      const petId = getPetId()
      
      if (!userId || !petId) {
        console.warn('User ID or Pet ID missing')
        return
      }
      
      const response = await getChatMessages(userId, petId)
      console.log('Loaded messages:', response)
      
      // Handle both response formats for backward compatibility
      const messagesList = response?.messages || response || []
      
      // Ensure messages have required fields and add unique ID
      // Remove duplicates based on timestamp + image_url combination
      const seen = new Set()
      const formattedMessages = messagesList
        .map((msg, idx) => {
          const id = msg.id || `${msg.timestamp || Date.now()}_${idx}_${msg.image_url || ''}`
          const uniqueKey = `${msg.timestamp || ''}_${msg.image_url || ''}_${msg.text?.substring(0, 50) || ''}`
          
          // Skip duplicates
          if (seen.has(uniqueKey)) {
            return null
          }
          seen.add(uniqueKey)
          
          return {
            id,
            sender: msg.sender || 'user',
            text: msg.text || '',
            image_url: msg.image_url || null,
            timestamp: msg.timestamp || new Date().toISOString()
          }
        })
        .filter(msg => msg !== null) // Remove null entries (duplicates)
      
      console.log('Formatted messages:', formattedMessages)
      setMessages(formattedMessages)
    } catch (err) {
      console.error('Failed to load messages:', err)
      // Keep existing messages if loading fails
      console.error('Error details:', err.response?.data || err.message)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage = {
      sender: 'user',
      text: input,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsTyping(true)

    try {
      const userId = getUserId()
      const petId = getPetId()
      const response = await sendChatMessage(userId, petId, input, petProfile)
      
      const aiMessage = {
        sender: 'ai',
        text: response.answer,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, aiMessage])
    } catch (err) {
      console.error('Failed to send message:', err)
      setMessages(prev => [...prev, {
        sender: 'ai',
        text: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      }])
    } finally {
      setIsTyping(false)
    }
  }

  const handleFileUpload = async (file, isImage = true) => {
    try {
      const userId = getUserId()
      const petId = getPetId()
      
      if (!file) {
        alert('Please select a file to upload.')
        return
      }
      
      // Validate file size (max 10MB)
      const maxSize = 10 * 1024 * 1024 // 10MB
      if (file.size > maxSize) {
        alert('File size is too large. Please upload an image smaller than 10MB.')
        return
      }
      
      // Validate file type for images
      if (isImage && !file.type.startsWith('image/')) {
        alert('Please upload a valid image file (jpg, png, etc.)')
        return
      }
      
      setIsTyping(true)
      
      if (isImage) {
        const response = await uploadImage(userId, petId, file)
        console.log('Upload successful:', response)
        
        // Clear file input to allow same file upload again
        if (imageInputRef.current) {
          imageInputRef.current.value = ''
        }
        
        // If response includes messages, add them immediately to chat
        if (response.messages && Array.isArray(response.messages) && response.messages.length > 0) {
          console.log('Adding messages from upload response:', response.messages)
          // Add unique IDs and ensure proper format
          const timestamp = Date.now()
          const formattedNewMessages = response.messages.map((msg, idx) => ({
            id: `${timestamp}_${idx}_${msg.image_url || ''}`,
            sender: msg.sender || 'user',
            text: msg.text || '',
            image_url: msg.image_url || null,
            timestamp: msg.timestamp || new Date().toISOString()
          }))
          
          // Add new messages and remove duplicates
          setMessages(prev => {
            const existingKeys = new Set(prev.map(m => `${m.timestamp}_${m.image_url}_${m.text?.substring(0, 50)}`))
            const newMsgs = formattedNewMessages.filter(m => {
              const key = `${m.timestamp}_${m.image_url}_${m.text?.substring(0, 50)}`
              return !existingKeys.has(key)
            })
            return [...prev, ...newMsgs]
          })
          
          // Also reload to ensure we have everything
          setTimeout(() => loadMessages(), 500)
        } else {
          // Fallback: reload messages if not included in response
          await new Promise(resolve => setTimeout(resolve, 500))
          await loadMessages()
          setTimeout(() => loadMessages(), 1000)
          setTimeout(() => loadMessages(), 2000)
        }
      } else {
        await uploadDocument(userId, petId, file)
        // Reload messages for documents too
        await new Promise(resolve => setTimeout(resolve, 500))
        await loadMessages()
      }
    } catch (err) {
      console.error('Upload failed:', err)
      const errorMessage = err.response?.data?.detail || err.message || 'Upload failed. Please try again.'
      alert(`Upload failed: ${errorMessage}`)
    } finally {
      setIsTyping(false)
    }
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <button onClick={() => navigate('/')} className="btn-back">← Back</button>
        <h1>💬 Chat</h1>
      </div>
      <div className="chat-messages">
        {messages.map((msg, idx) => {
          // Create unique key combining timestamp and index
          const uniqueKey = `${msg.timestamp || Date.now()}_${idx}_${msg.image_url || ''}`
          // Add cache busting parameter to image URL to prevent browser caching
          const imageSrc = msg.image_url 
            ? `http://localhost:8000${msg.image_url}?t=${msg.timestamp || Date.now()}&i=${idx}`
            : null
          
          return (
            <div key={uniqueKey} className={`message ${msg.sender === 'user' ? 'user-message' : 'ai-message'}`}>
              <div className="message-content">{msg.text}</div>
              {imageSrc && (
                <img 
                  src={imageSrc} 
                  alt="Uploaded" 
                  className="message-image"
                  key={imageSrc} // Force React to reload image if URL changes
                  onError={(e) => {
                    console.error('Image failed to load:', imageSrc)
                    e.target.style.display = 'none'
                  }}
                />
              )}
            </div>
          )
        })}
        {isTyping && (
          <div className="message ai-message">
            <div className="message-content typing">AI is typing...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input-container">
        <input
          type="file"
          ref={imageInputRef}
          accept="image/*"
          style={{ display: 'none' }}
          onChange={(e) => e.target.files[0] && handleFileUpload(e.target.files[0], true)}
        />
        <input
          type="file"
          ref={fileInputRef}
          accept=".pdf,.doc,.docx"
          style={{ display: 'none' }}
          onChange={(e) => e.target.files[0] && handleFileUpload(e.target.files[0], false)}
        />
        <button onClick={() => imageInputRef.current?.click()} className="btn-icon">📷</button>
        <button onClick={() => fileInputRef.current?.click()} className="btn-icon">📄</button>
        <form onSubmit={handleSend} className="chat-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your dog..."
            className="chat-input"
          />
          <button type="submit" className="btn-send">Send</button>
        </form>
      </div>
    </div>
  )
}

export default Chat


