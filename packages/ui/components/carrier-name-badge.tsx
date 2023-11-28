import { CARRIER_THEMES } from '@karrio/types';
import React from 'react';


interface CarrierNameBadgeComponent extends React.AllHTMLAttributes<HTMLDivElement> {
  carrier_name?: string;
  display_name: string | null;
}

export const CarrierNameBadge: React.FC<CarrierNameBadgeComponent> = ({ carrier_name, display_name, className, ...props }) => {
  const theme = CARRIER_THEMES[carrier_name || 'generic'] || 'is-generic';

  return (
    <div className={`${className} ${theme}`} {...props}>
      {display_name}
    </div>
  );
};
