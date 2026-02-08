import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/Common/Navbar';
import './AboutPage.css';
import {
  Gamepad2,
  BarChart3,
  Award,
  Users,
  Globe,
  Lock,
  Mail,
  Phone,
  Target,
  Sparkles,
  UsersRound
} from 'lucide-react';

/**
 * About Us Page
 * Information about the platform, team, and mission
 */
const AboutPage = () => {
  const { language } = useLanguage();

  const content = {
    uz: {
      title: 'Biz haqimizda',
      subtitle: 'Alif24 - 3-9 yoshli bolalar uchun adaptiv ta\'lim platformasi',
      mission: {
        title: 'Bizning maqsadimiz',
        text: 'Har bir bolaga zamonaviy, qiziqarli va samarali ta\'lim berish. Biz bolalarning individual xususiyatlarini hisobga olib, ularga eng mos ta\'lim usullarini taqdim etamiz.'
      },
      features: {
        title: 'Platformamiz imkoniyatlari',
        items: [
          {
            icon: <Gamepad2 size={64} className="text-purple-500 mx-auto" />,
            title: 'O\'yinlar orqali o\'rganish',
            desc: 'Bolalar uchun qiziqarli va ta\'limiy o\'yinlar'
          },
          {
            icon: <BarChart3 size={64} className="text-green-500 mx-auto" />,
            title: 'Adaptiv ta\'lim',
            desc: 'Har bir bolaning darajasiga moslashuvchi dastur'
          },
          {
            icon: <Award size={64} className="text-yellow-500 mx-auto" />,
            title: 'Yutuqlar va mukofotlar',
            desc: 'Motivatsiya uchun yutuqlar tizimi'
          },
          {
            icon: <Users size={64} className="text-blue-500 mx-auto" />,
            title: 'Ota-onalar uchun nazorat',
            desc: 'Bolalar progressini kuzatish imkoniyati'
          },
          {
            icon: <Globe size={64} className="text-cyan-500 mx-auto" />,
            title: 'Ko\'p tillilik',
            desc: 'O\'zbek, rus va ingliz tillarida'
          },
          {
            icon: <Lock size={64} className="text-red-500 mx-auto" />,
            title: 'Xavfsizlik',
            desc: 'Bolalar uchun xavfsiz muhit'
          }
        ]
      },
      team: {
        title: 'Bizning jamoa',
        text: 'Biz - tajribali dasturchilar, dizaynerlar va ta\'lim mutaxassislaridan iborat jamoa. Bizning maqsadimiz - O\'zbekiston bolalariga sifatli ta\'lim berish.'
      },
      contact: {
        title: 'Biz bilan bog\'laning',
        email: 'nuralisadullayevich@gmail.com',
        phone: '+998 90 827 83 58'

      }
    },
    ru: {
      title: 'О нас',
      subtitle: 'Alif24 - адаптивная образовательная платформа для детей 3-9 лет',
      mission: {
        title: 'Наша миссия',
        text: 'Предоставить каждому ребенку современное, интересное и эффективное образование. Мы учитываем индивидуальные особенности детей и предлагаем наиболее подходящие методы обучения.'
      },
      features: {
        title: 'Возможности платформы',
        items: [
          {
            icon: <Gamepad2 size={64} className="text-purple-500 mx-auto" />,
            title: 'Обучение через игры',
            desc: 'Интересные и образовательные игры для детей'
          },
          {
            icon: <BarChart3 size={64} className="text-green-500 mx-auto" />,
            title: 'Адаптивное обучение',
            desc: 'Программа адаптируется к уровню каждого ребенка'
          },
          {
            icon: <Award size={64} className="text-yellow-500 mx-auto" />,
            title: 'Достижения и награды',
            desc: 'Система достижений для мотивации'
          },
          {
            icon: <Users size={64} className="text-blue-500 mx-auto" />,
            title: 'Контроль для родителей',
            desc: 'Возможность отслеживать прогресс детей'
          },
          {
            icon: <Globe size={64} className="text-cyan-500 mx-auto" />,
            title: 'Многоязычность',
            desc: 'На узбекском, русском и английском языках'
          },
          {
            icon: <Lock size={64} className="text-red-500 mx-auto" />,
            title: 'Безопасность',
            desc: 'Безопасная среда для детей'
          }
        ]
      },
      team: {
        title: 'Наша команда',
        text: 'Мы - команда опытных разработчиков, дизайнеров и специалистов по образованию. Наша цель - предоставить качественное образование детям Узбекистана.'
      },
      contact: {
        title: 'Свяжитесь с нами',
        email: 'nuralisadullayevich@gmail.com',
        phone: '+998 90 827 83 58'
      }
    },
    en: {
      title: 'About Us',
      subtitle: 'Alif24 - Adaptive learning platform for children aged 3-9',
      mission: {
        title: 'Our Mission',
        text: 'To provide every child with modern, engaging, and effective education. We consider the individual characteristics of children and offer the most suitable learning methods.'
      },
      features: {
        title: 'Platform Features',
        items: [
          {
            icon: <Gamepad2 size={64} className="text-purple-500 mx-auto" />,
            title: 'Learning through games',
            desc: 'Fun and educational games for children'
          },
          {
            icon: <BarChart3 size={64} className="text-green-500 mx-auto" />,
            title: 'Adaptive learning',
            desc: 'Program adapts to each child\'s level'
          },
          {
            icon: <Award size={64} className="text-yellow-500 mx-auto" />,
            title: 'Achievements and rewards',
            desc: 'Achievement system for motivation'
          },
          {
            icon: <Users size={64} className="text-blue-500 mx-auto" />,
            title: 'Parental control',
            desc: 'Track children\'s progress'
          },
          {
            icon: <Globe size={64} className="text-cyan-500 mx-auto" />,
            title: 'Multilingual',
            desc: 'In Uzbek, Russian and English'
          },
          {
            icon: <Lock size={64} className="text-red-500 mx-auto" />,
            title: 'Safety',
            desc: 'Safe environment for children'
          }
        ]
      },
      team: {
        title: 'Our Team',
        text: 'We are a team of experienced developers, designers and education specialists. Our goal is to provide quality education to children of Uzbekistan.'
      },
      contact: {
        title: 'Contact Us',
        email: 'nuralisadullayevich@gmail.com',
        phone: '+998 90 827 83 58'
      }
    }
  };

  const t = content[language] || content.uz;

  return (
    <>
      <Navbar />
      <div className="about-page">
        {/* Hero Section */}
        <section className="about-hero">
          <h1 className="about-title">{t.title}</h1>
          <p className="about-subtitle">{t.subtitle}</p>
        </section>

        {/* Mission Section */}
        <section className="about-section mission-section">
          <div className="container">
            <h2 className="section-title flex items-center justify-center gap-3">
              <Target className="w-8 h-8 md:w-10 md:h-10 text-red-400" />
              {t.mission.title}
            </h2>
            <p className="section-text">{t.mission.text}</p>
          </div>
        </section>

        {/* Features Section */}
        <section className="about-section features-section">
          <div className="container">
            <h2 className="section-title flex items-center justify-center gap-3">
              <Sparkles className="w-8 h-8 md:w-10 md:h-10 text-yellow-400" />
              {t.features.title}
            </h2>
            <div className="features-grid">
              {t.features.items.map((item, index) => (
                <div key={index} className="feature-card">
                  <div className="feature-icon flex justify-center">{item.icon}</div>
                  <h3 className="feature-title">{item.title}</h3>
                  <p className="feature-desc">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Team Section */}
        <section className="about-section team-section">
          <div className="container">
            <h2 className="section-title flex items-center justify-center gap-3">
              <UsersRound className="w-8 h-8 md:w-10 md:h-10 text-purple-400" />
              {t.team.title}
            </h2>
            <p className="section-text">{t.team.text}</p>
          </div>
        </section>

        {/* Contact Section */}
        <section className="about-section contact-section">
          <div className="container">
            <h2 className="section-title flex items-center justify-center gap-3">
              <Mail className="w-8 h-8 md:w-10 md:h-10 text-blue-400" />
              {t.contact.title}
            </h2>
            <div className="contact-info">
              <div className="contact-item">
                <span className="contact-icon text-blue-400"><Mail size={48} /></span>
                <a href={`mailto:${t.contact.email}`} className="contact-link">
                  {t.contact.email}
                </a>
              </div>
              <div className="contact-item">
                <span className="contact-icon text-green-400"><Phone size={48} /></span>
                <a href={`tel:${t.contact.phone}`} className="contact-link">
                  {t.contact.phone}
                </a>
              </div>
            </div>
          </div>
        </section>
      </div>
    </>
  );
};

export default AboutPage;
