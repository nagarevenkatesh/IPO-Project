import React, {useState} from 'react'
import API from '../api'
import { useNavigate } from 'react-router-dom'

export default function Dashboard(){
  const [ticker,setTicker] = useState('')
  const [price,setPrice] = useState('')
  const [date,setDate] = useState('')
  const [exchange,setExchange] = useState('')
  const [sector,setSector] = useState('')
  const [result,setResult] = useState(null)
  const nav = useNavigate()

  function logout(){
    localStorage.removeItem('access_token')
    localStorage.removeItem('username')
    nav('/')
  }

  async function submit(e){
    e.preventDefault()
    try{
      const res = await API.post('/predict', {
        items: [{
          ticker,
          issue_price: parseFloat(price),
          listing_date: date,
          exchange,
          sector
        }]
      })
      setResult(res.data.results[0])
    }catch(err){
      setResult({error: err.response?.data?.detail || 'Prediction failed'})
    }
  }

  return (
    <div className="container">
      <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:12}}>
        <h2>Dashboard</h2>
        <div>
          <strong>{localStorage.getItem('username')||''}</strong>
          <button onClick={logout} style={{marginLeft:8}}>Logout</button>
        </div>
      </div>

      <div className="card" style={{marginBottom:12}}>
        <h3>IPO Prediction</h3>
        <form onSubmit={submit}>
          <input value={ticker} onChange={e=>setTicker(e.target.value)} placeholder="Ticker" />
          <input value={price} onChange={e=>setPrice(e.target.value)} placeholder="Issue Price (e.g. 120)" />
          <input value={date} onChange={e=>setDate(e.target.value)} placeholder="Listing Date (YYYY-MM-DD)" />
          <input value={exchange} onChange={e=>setExchange(e.target.value)} placeholder="Exchange (NSE/BSE/OTH)" />
          <input value={sector} onChange={e=>setSector(e.target.value)} placeholder="Sector (TECH/FIN/...)" />
          <button type="submit">Predict</button>
        </form>
      </div>

      <div className="card">
        <h3>Result</h3>
        {result ? (
          result.error ? <div style={{color:'red'}}>{result.error}</div> :
          <div>
            <div><strong>Ticker:</strong> {result.ticker}</div>
            <div><strong>Predicted first-day %:</strong> {result.predicted_firstday_pct.toFixed(2)}%</div>
          </div>
        ) : <div>No predictions yet</div>}
      </div>
    </div>
  )
}
