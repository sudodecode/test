package api

import "time"

// TokenBucket allows bursts up to Capacity and refills at Rate tokens per second.
type TokenBucket struct {
	Capacity float64
	Rate     float64
	tokens   float64
	last     time.Time
}

func (b *TokenBucket) Allow(now time.Time) bool {
	if b.last.IsZero() {
		b.tokens, b.last = b.Capacity, now
	}
	elapsed := min(now.Sub(b.last), time.Minute)
	b.tokens = min(b.Capacity, b.tokens+elapsed.Seconds()*b.Rate)
	b.last = now
	if b.tokens < 1 {
		return false
	}
	b.tokens--
	return true
}
// trigger 2026-10-10T08:06:01Z
