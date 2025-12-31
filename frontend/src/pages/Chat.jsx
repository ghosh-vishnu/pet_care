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
      const response = await getChatMessages(userId, petId)
      setMessages(response.messages || [])
    } catch (err) {
      console.error('Failed to load messages:', err)
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
      
      if (isImage) {
        await uploadImage(userId, petId, file)
      } else {
        await uploadDocument(userId, petId, file)
      }
      
      setTimeout(loadMessages, 1000)
    } catch (err) {
      console.error('Upload failed:', err)
      alert('Upload failed. Please try again.')
    }
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <button onClick={() => navigate('/')} className="btn-back">← Back</button>
        <h1>💬 Chat</h1>
      </div>
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.sender === 'user' ? 'user-message' : 'ai-message'}`}>
            <div className="message-content">{msg.text}</div>
            {msg.image_url && (
              <img src={`http://localhost:8000${msg.image_url}`} alt="Uploaded" className="message-image" />
            )}
          </div>
        ))}
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

