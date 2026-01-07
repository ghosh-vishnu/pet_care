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
  const isLoadingMessagesRef = useRef(false)

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

  const loadMessages = async (silent = false) => {
    // Prevent multiple simultaneous calls
    if (isLoadingMessagesRef.current) {
      if (!silent) console.log('loadMessages already in progress, skipping...')
      return
    }
    
    isLoadingMessagesRef.current = true
    
    try {
      const userId = getUserId()
      const petId = getPetId()
      
      if (!userId || !petId) {
        console.warn('User ID or Pet ID missing')
        return
      }
      
      const response = await getChatMessages(userId, petId)
      if (!silent) console.log('Loaded messages:', response)
      
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
        .sort((a, b) => {
          // Sort messages by timestamp to ensure correct chronological order
          const timeA = new Date(a.timestamp).getTime()
          const timeB = new Date(b.timestamp).getTime()
          return timeA - timeB
        })
      
      if (!silent) console.log('Formatted messages (sorted by timestamp):', formattedMessages)
      setMessages(formattedMessages)
    } catch (err) {
      console.error('Failed to load messages:', err)
      // Keep existing messages if loading fails
      console.error('Error details:', err.response?.data || err.message)
    } finally {
      isLoadingMessagesRef.current = false
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
      
      // Clear file input to allow same file upload again (before upload)
      if (imageInputRef.current) {
        imageInputRef.current.value = ''
      }
      
      if (isImage) {
        try {
          const response = await uploadImage(userId, petId, file)
          console.log('Upload successful:', response)
          
          // Check if response indicates validation failure (but still has messages)
          if (response.status === 'validation_failed' || response.status === 'error') {
            // Validation failed - messages are already in database, reload them
            // Don't show alert, just reload messages to show the error message in chat
            await new Promise(resolve => setTimeout(resolve, 300))
            await loadMessages(true) // silent mode
            setIsTyping(false)
            return // Exit early - don't continue with success flow
          }
          
          // Success case - If response includes messages, add them immediately to chat
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
            
            // Add new messages and remove duplicates, then sort by timestamp
            setMessages(prev => {
              const existingKeys = new Set(prev.map(m => `${m.timestamp}_${m.image_url}_${m.text?.substring(0, 50)}`))
              const newMsgs = formattedNewMessages.filter(m => {
                const key = `${m.timestamp}_${m.image_url}_${m.text?.substring(0, 50)}`
                return !existingKeys.has(key)
              })
              const allMessages = [...prev, ...newMsgs]
              // Sort by timestamp to maintain correct chronological order
              return allMessages.sort((a, b) => {
                const timeA = new Date(a.timestamp).getTime()
                const timeB = new Date(b.timestamp).getTime()
                return timeA - timeB
              })
            })
          } else {
            // Fallback: reload messages if not included in response (silent mode)
            await new Promise(resolve => setTimeout(resolve, 500))
            await loadMessages(true) // silent mode
          }
        } catch (err) {
          console.error('Upload failed:', err)
          
          // Check if it's a validation error (400) with messages in response
          if (err.response?.status === 400 && err.response?.data) {
            const errorData = err.response.data
            
            // If it's a validation failure, handle it specially - NO POPUP ALERT
            if (errorData.status === 'validation_failed') {
              console.log('Validation failed, handling messages from error response - NO ALERT')
              
              // If error response includes messages, display them immediately
              if (errorData.messages && Array.isArray(errorData.messages) && errorData.messages.length > 0) {
                const formattedNewMessages = errorData.messages.map((msg, idx) => ({
                  id: `${Date.now()}_${idx}_${msg.image_url || ''}`,
                  sender: msg.sender || 'user',
                  text: msg.text || '',
                  image_url: msg.image_url || null,
                  timestamp: msg.timestamp || new Date().toISOString()
                }))
                
                // Add messages to chat and sort by timestamp
                setMessages(prev => {
                  const existingKeys = new Set(prev.map(m => `${m.timestamp}_${m.image_url}_${m.text?.substring(0, 50)}`))
                  const newMsgs = formattedNewMessages.filter(m => {
                    const key = `${m.timestamp}_${m.image_url}_${m.text?.substring(0, 50)}`
                    return !existingKeys.has(key)
                  })
                  const allMessages = [...prev, ...newMsgs]
                  // Sort by timestamp to maintain correct order
                  return allMessages.sort((a, b) => {
                    const timeA = new Date(a.timestamp).getTime()
                    const timeB = new Date(b.timestamp).getTime()
                    return timeA - timeB
                  })
                })
                
                // NO ALERT - error message is shown in chat
                setIsTyping(false)
                return // Exit - error message will appear in chat
              } else {
                // Fallback: reload messages if not in response (silent mode)
                await new Promise(resolve => setTimeout(resolve, 300))
                await loadMessages(true) // silent mode
                setIsTyping(false)
                return
              }
            }
            
            // For other 400 errors, show alert
            const errorMessage = errorData.detail || errorData.message || 'Upload failed. Please try again.'
            alert(`Upload failed: ${errorMessage}`)
          } else {
            // For other errors (network, server, etc.), show alert
            const errorMessage = err.response?.data?.detail || err.message || 'Upload failed. Please try again.'
            alert(`Upload failed: ${errorMessage}`)
          }
        }
      } else {
        try {
          await uploadDocument(userId, petId, file)
          // Reload messages for documents too (silent mode)
          await new Promise(resolve => setTimeout(resolve, 500))
          await loadMessages(true) // silent mode
        } catch (err) {
          console.error('Document upload failed:', err)
          const errorMessage = err.response?.data?.detail || err.message || 'Upload failed. Please try again.'
          alert(`Upload failed: ${errorMessage}`)
        }
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


