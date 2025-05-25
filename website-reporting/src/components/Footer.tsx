import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="mt-16 py-8">
      <div className="container mx-auto px-4">
        <div className="text-center text-gray-600">
          <p className="text-sm">
            Made with curiosity and joy by{' '}
            <Link 
              href="https://declankramper.com?source=divvy_website"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 underline font-medium"
            >
              declan
            </Link>
            {' '}in the old town foxtrot — thanks fox trot! ☕️
          </p>
        </div>
      </div>
    </footer>
  );
} 