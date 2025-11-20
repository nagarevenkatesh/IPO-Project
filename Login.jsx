import React, {useState} from 'react'
import API from '../api'
import { useNavigate, Link } from 'react-router-dom'

export default function Login(){
  const [username,setUsername] = useState('')
  const [password,setPassword] = useState('')
  const [err,setErr] = useState('')
  const nav = useNavigate()

  async function submit(e){
    e.preventDefault()
    try{
      const res = await API.post('/login', {username, password})
      localStorage.setItem('access_token', res.data.access_token)
      localStorage.setItem('username', res.data.username)
      nav('/dashboard')
    }catch(err){
      setErr(err.response?.data?.detail || 'Login failed')
    }
  }

  return (
    <div className="container">
      <div className="card">
        <h2>Login</h2>
        {err && <div style={{color:'red'}}>{err}</div>}
        <form onSubmit={submit}>
          <input value={username} onChange={e=>setUsername(e.target.value)} placeholder="username" />
          <input value={password} onChange={e=>setPassword(e.target.value)} placeholder="password" type="password" />
          <button type="submit">Login</button>
        </form>
        <p>Don't have an account? <Link to="/register">Register</Link></p>
      </div>
    </div>
  )
}
