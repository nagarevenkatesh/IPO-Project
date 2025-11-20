import React, {useState} from 'react'
import API from '../api'
import { useNavigate, Link } from 'react-router-dom'

export default function Register(){
  const [username,setUsername] = useState('')
  const [password,setPassword] = useState('')
  const [msg,setMsg] = useState('')
  const nav = useNavigate()

  async function submit(e){
    e.preventDefault()
    try{
      await API.post('/register', {username, password})
      setMsg('Registered. You can now login.')
      setTimeout(()=>nav('/'), 800)
    }catch(err){
      setMsg(err.response?.data?.detail || 'Register failed')
    }
  }

  return (
    <div className="container">
      <div className="card">
        <h2>Register</h2>
        {msg && <div>{msg}</div>}
        <form onSubmit={submit}>
          <input value={username} onChange={e=>setUsername(e.target.value)} placeholder="username" />
          <input value={password} onChange={e=>setPassword(e.target.value)} placeholder="password" type="password" />
          <button type="submit">Register</button>
        </form>
        <p>Have an account? <Link to="/">Login</Link></p>
      </div>
    </div>
  )
}
