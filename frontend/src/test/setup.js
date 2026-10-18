import '@testing-library/jest-dom/vitest'

// React Flow measures container size via ResizeObserver, which jsdom
// doesn't implement. A no-op stub is enough for rendering tests that
// don't depend on actual layout measurements.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
global.ResizeObserver = ResizeObserverStub
