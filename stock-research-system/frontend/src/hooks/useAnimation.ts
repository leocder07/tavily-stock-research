import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * Custom hook for scroll-triggered animations
 */
export const useScrollAnimation = (threshold = 0.1) => {
  const elementRef = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible(true);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold }
    );

    const currentElement = elementRef.current;
    if (currentElement) {
      observer.observe(currentElement);
    }

    return () => {
      if (currentElement) {
        observer.unobserve(currentElement);
      }
    };
  }, [threshold]);

  return { ref: elementRef, isVisible };
};

/**
 * Custom hook for count-up animations
 */
export const useCountUp = (
  end: number,
  duration: number = 2000,
  start: number = 0,
  decimals: number = 0
) => {
  const [count, setCount] = useState(start);
  const [isAnimating, setIsAnimating] = useState(false);

  const animate = useCallback(() => {
    setIsAnimating(true);
    const startTime = Date.now();
    const endTime = startTime + duration;

    const timer = setInterval(() => {
      const now = Date.now();
      const remaining = Math.max(endTime - now, 0);
      const progress = 1 - remaining / duration;
      
      // Easing function (ease-out-cubic)
      const easeOutCubic = 1 - Math.pow(1 - progress, 3);
      const currentCount = start + (end - start) * easeOutCubic;

      if (progress === 1) {
        setCount(end);
        setIsAnimating(false);
        clearInterval(timer);
      } else {
        setCount(parseFloat(currentCount.toFixed(decimals)));
      }
    }, 16); // 60fps

    return () => clearInterval(timer);
  }, [end, duration, start, decimals]);

  return { count, animate, isAnimating };
};

/**
 * Custom hook for spring animations
 */
export const useSpring = (
  initialValue: number,
  config = { stiffness: 100, damping: 10, mass: 1 }
) => {
  const [value, setValue] = useState(initialValue);
  const [velocity, setVelocity] = useState(0);
  const animationRef = useRef<number | undefined>(undefined);

  const animateTo = useCallback((target: number) => {
    let currentValue = value;
    let currentVelocity = velocity;

    const animate = () => {
      const { stiffness, damping, mass } = config;
      
      // Spring physics
      const force = (target - currentValue) * stiffness;
      const dampingForce = -currentVelocity * damping;
      const acceleration = (force + dampingForce) / mass;
      
      currentVelocity += acceleration * 0.001;
      currentValue += currentVelocity;

      setValue(currentValue);
      setVelocity(currentVelocity);

      // Continue animation if not settled
      if (Math.abs(currentVelocity) > 0.01 || Math.abs(target - currentValue) > 0.01) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
    animationRef.current = requestAnimationFrame(animate);
  }, [value, velocity, config]);

  return { value, animateTo };
};

/**
 * Custom hook for parallax effects
 */
export const useParallax = (speed: number = 0.5) => {
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const scrolled = window.scrollY;
      setOffset(scrolled * speed);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [speed]);

  return offset;
};

/**
 * Custom hook for mouse position tracking
 */
export const useMousePosition = () => {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setPosition({ x: e.clientX, y: e.clientY });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return position;
};

/**
 * Custom hook for gesture detection
 */
export const useGesture = (elementRef: React.RefObject<HTMLElement>) => {
  const [gesture, setGesture] = useState<string | null>(null);
  const touchStart = useRef<{ x: number; y: number; time: number } | null>(null);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const handleTouchStart = (e: TouchEvent) => {
      touchStart.current = {
        x: e.touches[0].clientX,
        y: e.touches[0].clientY,
        time: Date.now(),
      };
    };

    const handleTouchEnd = (e: TouchEvent) => {
      if (!touchStart.current) return;

      const touchEnd = {
        x: e.changedTouches[0].clientX,
        y: e.changedTouches[0].clientY,
        time: Date.now(),
      };

      const deltaX = touchEnd.x - touchStart.current.x;
      const deltaY = touchEnd.y - touchStart.current.y;
      const deltaTime = touchEnd.time - touchStart.current.time;

      // Detect swipe gestures
      if (deltaTime < 500) {
        if (Math.abs(deltaX) > Math.abs(deltaY)) {
          if (Math.abs(deltaX) > 50) {
            setGesture(deltaX > 0 ? 'swipe-right' : 'swipe-left');
          }
        } else {
          if (Math.abs(deltaY) > 50) {
            setGesture(deltaY > 0 ? 'swipe-down' : 'swipe-up');
          }
        }
      }

      // Reset gesture after a delay
      setTimeout(() => setGesture(null), 500);
      touchStart.current = null;
    };

    element.addEventListener('touchstart', handleTouchStart);
    element.addEventListener('touchend', handleTouchEnd);

    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchend', handleTouchEnd);
    };
  }, [elementRef]);

  return gesture;
};

/**
 * Custom hook for stagger animations
 */
export const useStaggerAnimation = (itemCount: number, delay: number = 100) => {
  const [visibleItems, setVisibleItems] = useState<number[]>([]);

  useEffect(() => {
    const timers: NodeJS.Timeout[] = [];

    for (let i = 0; i < itemCount; i++) {
      const timer = setTimeout(() => {
        setVisibleItems((prev) => [...prev, i]);
      }, i * delay);
      timers.push(timer);
    }

    return () => {
      timers.forEach(clearTimeout);
    };
  }, [itemCount, delay]);

  return visibleItems;
};

/**
 * Custom hook for typewriter effect
 */
export const useTypewriter = (text: string, speed: number = 50) => {
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const startTyping = useCallback(() => {
    setIsTyping(true);
    setDisplayedText('');
    
    let currentIndex = 0;
    const timer = setInterval(() => {
      if (currentIndex < text.length) {
        setDisplayedText(text.slice(0, currentIndex + 1));
        currentIndex++;
      } else {
        setIsTyping(false);
        clearInterval(timer);
      }
    }, speed);

    return () => clearInterval(timer);
  }, [text, speed]);

  return { displayedText, isTyping, startTyping };
};

/**
 * Custom hook for shake animation
 */
export const useShake = () => {
  const [isShaking, setIsShaking] = useState(false);

  const shake = useCallback((duration: number = 500) => {
    setIsShaking(true);
    setTimeout(() => setIsShaking(false), duration);
  }, []);

  const shakeStyles = isShaking
    ? {
        animation: 'shake 0.5s',
        animationIterationCount: 1,
      }
    : {};

  return { shake, shakeStyles, isShaking };
};